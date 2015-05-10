"""
GilSearcher.py

This program takes in a series of predefined queries and uses the index built by Whoosh,
as well as that library's search functions, to return relevant documents according to the
given query. Queries are in turn altered by the each of the algorithms described in Indexer:

Using the (non stop-word) terms in plaintext,
Stemming the terms using a Porter and Snowball stemming algorithm,
k-gramming the terms in the document (4-gram and 5-gram).

Once the documents have been searched with every query using each tagging method,
the average precision is calculated on the results; that is, the top 10 documents returned 
by each query. These average precisions are averaged to achieve the Mean Average Precision.

The results can be found in experiment_results.txt.
"""
import sys, os, re
import nltk, nltk.corpus, whoosh, string
from nltk.corpus import stopwords
from nltk import PorterStemmer, SnowballStemmer
from whoosh import index, scoring
from whoosh.qparser import QueryParser

kgram_number = 4

p_s = PorterStemmer()
s_s = SnowballStemmer("english")

def alter_query(query, index_type):
	query_toks = query.split(" ")
	#print(query_toks)
	new_query_string = ""
	if index_type == "Unstemmed":
		for tok in query_toks:
			if new_query_string is not "":
				new_query_string = new_query_string + " " + tok
			else:
				new_query_string = tok

	elif index_type == "Porter":
		for tok in query_toks:
			tok = p_s.stem(tok)
			if new_query_string is not "":
				new_query_string = new_query_string + " " + tok
			else:
				new_query_string = tok

	elif index_type == "Snowball":
		for tok in query_toks:
			tok = s_s.stem(tok)
			if new_query_string is not "":
				new_query_string = new_query_string + " " + tok
			else:
				new_query_string = tok
	
	elif "kgram" in index_type:
		if "4" in index_type:
			kgram_number = 4
		else:
			kgram_number = 5

		for tok in query_toks:
			tok = s_s.stem(tok)
			k = len(tok) - kgram_number
			for i in range(0, k + 1):
				gram = tok[i:i+kgram_number]
		
				if new_query_string is not "":
					new_query_string = new_query_string + " " + gram
				else:
					new_query_string = gram
	
#	print(new_query_string)
	return new_query_string

relevances = {}

powers = [1, 5, 25, 125, 625] # weight more lengthy query appearances higher
queries = []

RELEVANCE_THRESHOLD = powers[0]*powers[1] - 2*powers[0]

with open("queries.txt", "r") as inFile:
	for line in inFile:
		queries.append(line.strip())

def formString(toks):
	sb = toks[0]
	for each in toks[1:]:
		sb = sb + " " + each
	return sb

def calcRelevance(query, path):
	score = 0

	with open(path, "r") as inFile:
		doc = inFile.read().lower()
		qterms = query.split(" ")
		n_qterms = len(qterms)

		for i in range(1, n_qterms + 1):
			for j in range(0, n_qterms - i + 1):
				q = formString(qterms[j:j + i])
				if q in doc:
					score = score + powers[i - 1]

	return score

def calcRelevances():
	for root, subFolders, files in os.walk("Reuters/test"):
		for file1 in files:
			filePath = root + "/" + file1
			for query in queries:
				qterms = query.split(" ")
				found = False
				for term in qterms:
					if term in root:
						c = calcRelevance(query, filePath)
						if c >= RELEVANCE_THRESHOLD:
							relevances[query][filePath] = c
						found = True
					if not found:
						c = calcRelevance(query, filePath)
						if c >= RELEVANCE_THRESHOLD:
							relevances[query][filePath] = c

def calculateAveragePrecision(query, results):
	precision = 0.0
	relevant_docs = 0.0
	doc_num = 1.0
	for result in results:
		try: 
			score = relevances[query][result["docId"]]
			if score >= RELEVANCE_THRESHOLD:
				relevant_docs = relevant_docs + 1
				precision = precision + relevant_docs/doc_num

		except:
			pass
		doc_num = doc_num + 1

	return precision

for query in queries:
	relevances[query] = {}
calcRelevances()
#for query in queries:
#	print(str(len(relevances[query].keys())) + " is the number of relevant docs for query " + query)

experiment = { "Unstemmed": {}, "Porter": {}, "Snowball": {}, "kgram4": {}, "kgram5": {} }

index_types = ["Unstemmed", "Porter", "Snowball", "kgram4", "kgram5"]
for index_type in index_types:
	ix = index.open_dir("indices/" + index_type + "_Index")
	qp = QueryParser("tags", schema=ix.schema)
	
	with ix.searcher() as searcher:
		for query in queries:

			results = searcher.search(qp.parse(alter_query(query, index_type)), limit=10, terms=True)
			prec = calculateAveragePrecision(query, results)
			rel_docs = len(relevances[query].keys())
			if rel_docs is not 0:
				#print("precision b4 avging is", prec)
				avg_prec = float(prec)/len(relevances[query].keys())
				experiment[index_type][query] = avg_prec
			else:
				pass

for each in experiment:
	print(each)
	print(experiment[each])
	score = 0
	for doc in experiment[each]:
		score = score + experiment[each][doc]

	doc_count =	len(experiment[each].keys())
	print("Mean Average Precision: " + str((score + 0.0)/doc_count))
