import requests

from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import spacy
from collections import Counter
from io import BytesIO
import base64
from textblob import TextBlob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from flask_cors import CORS
from wordcloud import WordCloud

# Load NLP model
nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
CORS(app)

# Selenium WebDriver setup
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_reviews():
    product_url = request.form['url']
    product_data = scrape_amazon(product_url)

    if product_data:
        sentiment_graph = generate_sentiment_graph(product_data['sentiment'])
        wordcloud_img = generate_wordcloud(product_data['all_reviews'])
        category_graph = generate_category_graph(product_data['category_counts'])

        return jsonify({
            'product_name': product_data['product_name'],
            'product_image': product_data['product_image'],
            'rating': product_data['rating'],
            'rating_stars': convert_rating_to_stars(product_data['rating']),
            'price': product_data['price'],
            'total_reviews': product_data['total_reviews'],
            'positive_percentage': product_data['positive_percentage'],
            'negative_percentage': product_data['negative_percentage'],
            'best_review': product_data['best_review'],
            'worst_review': product_data['worst_review'],
            'sentiment_graph': sentiment_graph,
            'wordcloud': wordcloud_img,
            'category_graph': category_graph
        })
    else:
        return jsonify({'error': 'Product not found'})

def scrape_amazon(url):
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    product_name = soup.find('span', {'id': 'productTitle'})
    product_name = product_name.get_text(strip=True) if product_name else "Unknown Product"

    image_element = soup.find('img', {'id': 'landingImage'})
    product_image = image_element['src'] if image_element else None

    rating_element = soup.find('span', {'class': 'a-icon-alt'})
    rating = rating_element.get_text(strip=True).split()[0] if rating_element else None

    try:
        rating = float(rating) if rating else None
    except ValueError:
        rating = None

    price_element = soup.find('span', {'id': 'priceblock_ourprice'}) or \
                    soup.find('span', {'id': 'priceblock_dealprice'}) or \
                    soup.find('span', {'class': 'a-price-whole'})

    price = price_element.get_text(strip=True) if price_element else "Price Not Available"

    reviews = get_reviews_from_amazon(url)
    total_reviews = len(reviews)

    sentiment, positive_percentage, negative_percentage, best_review, worst_review = perform_sentiment_analysis(reviews)
    category_counts = classify_review_topics(reviews)

    return {
        'product_name': product_name,
        'product_image': product_image,
        'rating': rating if rating else "No rating available",
        'price': price,
        'total_reviews': total_reviews,
        'positive_percentage': positive_percentage,
        'negative_percentage': negative_percentage,
        'sentiment': sentiment,
        'all_reviews': reviews,
        'best_review': best_review,
        'worst_review': worst_review,
        'category_counts': category_counts
    }

def get_reviews_from_amazon(url):
    driver.get(url)
    reviews = []
    try:
        review_elements = driver.find_elements(By.XPATH, "//span[@data-hook='review-body']")
        for review_element in review_elements:
            review_text = review_element.text
            if review_text:
                reviews.append(review_text)
    except Exception as e:
        print(f"Error scraping reviews: {e}")
    return reviews

def perform_sentiment_analysis(reviews):
    sentiments = {'positive': 0, 'negative': 0}
    review_scores = []

    for review in reviews:
        analysis = TextBlob(review)
        polarity = analysis.sentiment.polarity
        review_scores.append((review, polarity))

        if polarity > 0:
            sentiments['positive'] += 1
        else:
            sentiments['negative'] += 1

    review_scores.sort(key=lambda x: x[1], reverse=True)

    best_review = review_scores[0][0] if review_scores else "No best review available"
    worst_review = review_scores[-1][0] if review_scores else "No worst review available"

    total_reviews = len(reviews)
    positive_percentage = (sentiments['positive'] / total_reviews) * 100 if total_reviews > 0 else 0
    negative_percentage = (sentiments['negative'] / total_reviews) * 100 if total_reviews > 0 else 0

    return sentiments, round(positive_percentage, 2), round(negative_percentage, 2), best_review, worst_review

def generate_sentiment_graph(sentiment_data):
    labels = sentiment_data.keys()
    sizes = sentiment_data.values()

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['green', 'red'])
    plt.title('Sentiment Analysis of Reviews')

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generate_wordcloud(reviews):
    text = " ".join(reviews)
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

    buf = BytesIO()
    wordcloud.to_image().save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def generate_category_graph(category_counts):
    if not category_counts:
        return ""

    labels, values = zip(*category_counts.items())

    plt.figure(figsize=(8, 4))
    plt.bar(labels, values, color=['blue', 'green', 'red', 'purple', 'orange'])
    plt.xlabel("Categories")
    plt.ylabel("Mentions")
    plt.title("Review Topic Analysis")

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def classify_review_topics(reviews):
    keywords = ["sound", "bass", "comfort", "quality", "durability", "battery","Excellent", "Satisfied", "Amazing","Worth it", "Happy", "Best","Bad", "Disappointed", "Worst", "Useless", "Waste", "Poor","Worth it", "Costly", "Budget-friendly","Fast"," Slow", "Efficient"," Laggy"," Powerful", "Useless", "Feature-rich","Excellent Service","Fast delivery"," Late"," Well-packed", "Damaged", "Secure packaging", "Unsealed"]
    category_counts = Counter()

    for review in reviews:
        doc = nlp(review.lower())
        for token in doc:
            if token.text in keywords:
                category_counts[token.text] += 1

    return category_counts

def convert_rating_to_stars(rating):
    if isinstance(rating, float):
        full_stars = int(rating)
        half_star = "★" if rating - full_stars >= 0.5 else "☆"
        return "★" * full_stars + half_star + "☆" * (5 - full_stars - 1)
    return "No rating available"

if __name__ == '__main__':
    app.run(debug=True)
