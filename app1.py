from flask import Flask, render_template, request, jsonify
import praw
import google.generativeai as genai

app = Flask(__name__)

# --- Configure APIs ---
reddit = praw.Reddit(
    client_id="1FwX68jsXlIk1JT0P6KlGg",         
    client_secret="iqDXjaTAajkXHP1Xg7mhywkQiEChJg",
    user_agent="Sentimental_Analysis_Bot"
)

genai.configure(api_key="AIzaSyDZADUzhcw4kqjPLlgRqoesohZbIRiXJqU")
model = genai.GenerativeModel("gemini-1.0-pro")

@app.route('/')
def home():
    return render_template('main.html')  # This is now the homepage

@app.route('/index')
def index():
    return render_template('index.html')  # This contains the form and analysis logic

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    topic = data.get('topic', '').strip()
    category = data.get('category', '').strip()

    if not topic or not category:
        return jsonify({"error": "Please enter a topic and select a category!"})

    # Determine subreddit based on category
    category_subreddits = {
        "travel": "travel",
        "education": "all",
        "video_games": "all",
        "electronics": "appliances"
    }

    subreddit_name = category_subreddits.get(category)
    if not subreddit_name:
        return jsonify({"error": "Invalid category selected!"})

    # Fetch Reddit comments
    subreddit = reddit.subreddit(subreddit_name)
    posts = subreddit.search(topic, sort="top", limit=4)

    comments_data = []
    for post in posts:
        post.comments.replace_more(limit=0)
        comments = [comment.body for comment in post.comments[:7]]
        comments_data.append("\n".join(comments))

    comment_text = "\n".join(comments_data)

    if not comment_text.strip():
        return jsonify({"error": "No relevant data found on Reddit!"})

    # Generate AI-based analysis
    category_prompts = {
        "travel": f"Give a detailed analysis about traveling to {topic} based on user opinions. Include:\n1. Overview\n2. Best experiences\n3. Negative aspects\n4. Tips and suggestions.",
        "education": f"Analyze reviews of the {topic} course. Think from a perspective of a course Creator. Provide:\n1. Course overview\n2. Positive aspects\n3. Negative aspects\n4.What are the drawbacks of currently present courses from instructor perspective? ",
        "video_games": f"Analyze user feedback on the video game {topic}. Include:\n1. Game overview\n2. Strengths (gameplay, graphics, mechanics)\n3. Weaknesses\n4. Final verdict.",
        "electronics": f"Review the electronic product {topic}. Provide:\n1. Product overview\n2. Positive features\n3. Drawbacks\n4. Buying advice."
    }

    prompt = category_prompts[category] + f"\n\nReddit User Comments:\n{comment_text}"

    try:
        response = model.generate_content(prompt)
        result = response.text.replace("*", "")
    except Exception as e:
        return jsonify({"error": str(e)})

    return jsonify({"response": result})

if __name__ == '__main__':
    app.run(debug=True)
