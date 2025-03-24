import os
import re
from collections import defaultdict
import argparse

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

class IRSystemWhoosh:
    def __init__(self, articles_folder="articles_txt", index_dir="indexdir"):
        self.articles_folder = articles_folder
        self.index_dir = index_dir
        self.schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True), path=ID(stored=True))
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)
            self.ix = create_in(self.index_dir, self.schema)
            self.index_documents()
        else:
            self.ix = open_dir(self.index_dir)
        self.documents = self.load_documents()
        self.doc_ids = list(self.documents.keys())
        self.vectorizer, self.tfidf_matrix = self.build_vector_space()
    
    def index_documents(self):
        # Used ChatGPT for this part
        writer = self.ix.writer()
        for filename in os.listdir(self.articles_folder):
            if filename.endswith(".txt"):
                path = os.path.join(self.articles_folder, filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                writer.add_document(title=filename, content=content, path=path)
        writer.commit()
        print("Indexing done.")

    def load_documents(self):
        docs = {}
        for filename in os.listdir(self.articles_folder):
            if filename.endswith(".txt"):
                path = os.path.join(self.articles_folder, filename)
                with open(path, "r", encoding="utf-8") as f:
                    docs[filename] = f.read()
        return docs

    def boolean_query(self, query_str):
        with self.ix.searcher() as searcher:
            parser = QueryParser("content", schema=self.ix.schema)
            query = parser.parse(query_str)
            results = searcher.search(query, limit=None)
            print(f"Requests : {query_str} -> {len(results)} result(s).")
            for result in results:
                print(f"{result['title']} - score: {result.score:.4f}")
            return results
        
    def build_vector_space(self):
        vectorizer = TfidfVectorizer(stop_words='english')
        doc_texts = list(self.documents.values())
        tfidf_matrix = vectorizer.fit_transform(doc_texts)
        return vectorizer, tfidf_matrix
        
    def vector_query(self, query_str):
        query_vector = self.vectorizer.transform([query_str])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        ranked_indices = similarities.argsort()[::-1]
        ranked_results = [(self.doc_ids[i], similarities[i]) for i in ranked_indices if similarities[i] > 0]
        print(f"Vector Space Request : '{query_str}' -> {len(ranked_results)} result(s).")
        for doc, score in ranked_results:
            print(f"{doc} - score: {score:.4f}")
        return ranked_results

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--usage", action="store_true", help="Print usage instructions and exit.")
    args = argparser.parse_args()
    if args.usage:
        print("Usage: python IrSystem.py")
        print("Type of Boolean Request (exemple): '(test OR test2) AND openai'")
        print("Type of Vector Space Request: 'vector word1 word2 ...'")
        exit()
        
    ir_system = IRSystemWhoosh(articles_folder="articles_txt", index_dir="indexdir")
    
    while True:
        query_str = input("Request ('quit' or 'q' to exit) : ")
        if query_str == "q" or query_str == "quit":
            break
        if query_str.lower().startswith("vector"):
            query_text = query_str[7:].strip()
            print(query_text)
            results = ir_system.vector_query(query_text)
        else:
            results = ir_system.boolean_query(query_str)
