# Evaluation Guide

## Metrics

### Retrieval Metrics

- **Precision@k**: Fraction of retrieved documents that are relevant
- **Recall@k**: Fraction of relevant documents that are retrieved
- **MRR (Mean Reciprocal Rank)**: Average of reciprocal ranks
- **NDCG@k**: Normalized Discounted Cumulative Gain

### Generation Metrics

- **BLEU**: Overlap with reference answers
- **ROUGE**: Recall-based overlap metrics
- **BERTScore**: Semantic similarity using BERT
- **Answer Relevance**: Human evaluation scores

## Running Evaluations

### Quick Evaluation

```bash
python eval/runner.py --dataset eval/datasets/sample_qa.json