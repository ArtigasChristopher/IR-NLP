import re
import json
import os

def safe_filename(filename):
    # Remplace les caractères interdits sur Windows : \ / : * ? " < > |
    return re.sub(r'[\\/:*?"<>|]', '-', filename)

def load_articles(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        return json.load(file)

def save_articles_as_txt(articles, output_dir="articles_txt"):
    os.makedirs(output_dir, exist_ok=True)
    untitled_count = 0
    
    for i, article in enumerate(articles):
        title = article.get("title", "No title").strip()
        content = article.get("content", "No content available").strip()
        
        if title == "No title":
            title = f"untitled_{untitled_count}"
            untitled_count += 1
        
        safe_title = safe_filename("_".join(title.split()))
        file_path = os.path.join(output_dir, f"{safe_title}.txt")
        
        with open(file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(content)
    
    print(f"{len(articles)} files created in '{output_dir}'.")

def main():
    json_file = "articles_ai.json"
    articles = load_articles(json_file)
    save_articles_as_txt(articles)

if __name__ == "__main__":
    main()
