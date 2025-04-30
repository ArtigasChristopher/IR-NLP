import os
import sys
import json
from whoosh.qparser import QueryParser
from IRSystem import IRSystemWhoosh

class PrecisionRecallEvaluator:
    def __init__(self, ir_system, ground_truth=None, mode="boolean", top_k=10):
        self.ir_system = ir_system
        self.ground_truth = ground_truth or {}
        self.results = {}
        self.mode = mode
        self.top_k = top_k

    def add_ground_truth(self, query, relevant_docs):
        self.ground_truth[query] = relevant_docs

    def evaluate_query(self, query):
        if self.mode == "boolean":
            with self.ir_system.ix.searcher() as searcher:
                parser = QueryParser("content", schema=self.ir_system.ix.schema)
                parsed_query = parser.parse(query)
                results = searcher.search(parsed_query, limit=None)
                retrieved_docs = [result['title'] for result in results]
        elif self.mode == "lsi":
            results = self.ir_system.lsi_query(query)
            retrieved_docs = [doc_id for doc_id, _ in results[:self.top_k]]
        else:
            raise ValueError("Unknown mode, must be 'boolean' or 'lsi'")

        if query not in self.ground_truth:
            return None, None, None, retrieved_docs

        relevant_docs = self.ground_truth[query]
        true_positives = set(retrieved_docs).intersection(set(relevant_docs))

        precision = len(true_positives) / len(retrieved_docs) if retrieved_docs else 0
        recall = len(true_positives) / len(relevant_docs) if relevant_docs else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        self.results[query] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'retrieved': retrieved_docs,
            'relevant': relevant_docs,
            'true_positives': list(true_positives)
        }

        return precision, recall, f1_score, retrieved_docs

    def evaluate_all_queries(self):
        for query in self.ground_truth:
            self.evaluate_query(query)
        return self.results

    def print_evaluation_results(self, query=None):
        if query:
            if query in self.results:
                result = self.results[query]
                print(f"\nResult for query: '{query}'")
                print(f"Precision: {result['precision']:.4f}")
                print(f"Recall: {result['recall']:.4f}")
                print(f"F1-score: {result['f1_score']:.4f}")
                print(f"Retrieved documents ({len(result['retrieved'])}): {result['retrieved']}")
                print(f"Relevant documents ({len(result['relevant'])}): {result['relevant']}")
                print(f"TP ({len(result['true_positives'])}): {result['true_positives']}")
            else:
                print(f"No result for this query: {query}")
        else:
            avg_precision = sum(r['precision'] for r in self.results.values()) / len(self.results) if self.results else 0
            avg_recall = sum(r['recall'] for r in self.results.values()) / len(self.results) if self.results else 0
            avg_f1 = sum(r['f1_score'] for r in self.results.values()) / len(self.results) if self.results else 0

            print(f"\nEvaluation results for mode: {self.mode.upper()}")
            print(f"Number of evaluated requests: {len(self.results)}")
            print(f"Average Precision: {avg_precision:.4f}")
            print(f"Average Recall: {avg_recall:.4f}")
            print(f"Average F1-score: {avg_f1:.4f}")

            for query, result in self.results.items():
                print(f"\nQuery: '{query}'")
                print(f"  Precision: {result['precision']:.4f}")
                print(f"  Recall: {result['recall']:.4f}")
                print(f"  F1-score: {result['f1_score']:.4f}")
                print(f"  Retrieved: {len(result['retrieved'])} docs")
                print(f"  Relevant: {len(result['relevant'])} docs")
                print(f"  True Positives: {len(result['true_positives'])}")

    def save_results_to_json(self, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved in {output_file}")

def identify_relevant_documents(articles_folder, queries):
    ground_truth = {}

    for filename in os.listdir(articles_folder):
        if filename.endswith(".txt"):
            path = os.path.join(articles_folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().lower()

                for query, terms in queries.items():
                    if query not in ground_truth:
                        ground_truth[query] = []

                    is_relevant = True
                    for term, required in terms:
                        term_present = term.lower() in content
                        if required and not term_present:
                            is_relevant = False
                            break
                        elif not required and term_present:
                            is_relevant = True
                            break

                    if is_relevant:
                        ground_truth[query].append(filename)

    return ground_truth

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))
    articles_folder = os.path.join(base_path, "articles_txt")
    index_dir = os.path.join(base_path, "indexdir")

    ir_system = IRSystemWhoosh(articles_folder=articles_folder, index_dir=index_dir)

    queries = {
        "AI": [("AI", True)],
        "Nvidia": [("Nvidia", True)],
        "AI AND Nvidia": [("AI", True), ("Nvidia", True)],
        "AI OR Google": [("AI", False), ("Google", False)],
        "open-source": [("open-source", True)],
        "AI AND open-source": [("AI", True), ("open-source", True)],
        "BANANA": [("BANA", True)],
    }

    ground_truth = identify_relevant_documents(articles_folder, queries)

    evaluator_bool = PrecisionRecallEvaluator(ir_system, ground_truth, mode="boolean")
    evaluator_bool.evaluate_all_queries()
    print("=== BOOLEAN IR EVALUATION ===")
    evaluator_bool.print_evaluation_results()
    evaluator_bool.save_results_to_json(os.path.join(base_path, "boolean_evaluation_results.json"))

    evaluator_lsi = PrecisionRecallEvaluator(ir_system, ground_truth, mode="lsi", top_k=10)
    evaluator_lsi.evaluate_all_queries()
    print("\n=== LSI IR EVALUATION ===")
    evaluator_lsi.print_evaluation_results()
    evaluator_lsi.save_results_to_json(os.path.join(base_path, "lsi_evaluation_results.json"))
