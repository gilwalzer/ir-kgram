"""
GilIndexer.py

This program creates an index, in a selected folder (here, subfolders of an existing indices folder), of 
an existing collection of documents. The documents are tagged in the index using a variety of methods:

Using the (non stop-word) terms in plaintext,
Stemming the terms using a Porter and Snowball stemming algorithm,
k-gramming the terms in the document (4-gram and 5-gram).

The python library Whoosh is used to build the index.
"""
import sys, os, re
import nltk, nltk.corpus, whoosh, string
from nltk.corpus import stopwords
from nltk import PorterStemmer, SnowballStemmer
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED

p_s = PorterStemmer()
s_s = SnowballStemmer("english")
kgram_numbers = [4, 5] #int(sys.argv[1])
translate_tab = string.maketrans("","")

stops = stopwords.words("english")
stopset = set()
for each in stops:
	stopset.add(each)

my_schema = Schema(docId=ID(stored=True),
                title=TEXT(stored=True),
                body=TEXT(),
                tags=KEYWORD(stored=True))

def strip_content(content):
	sb = ""
	title = ""
	c = content.split("\n")
	for line in c:
		if line is not "\n" and line is not "" and len(line) > 1:
			title = line.rstrip()
			print (title)
			break
	for line in c:
		try:
			q = line.decode('ascii')
			sb = sb + line.rstrip() + "\n"
		except:
			pass
	return sb, title

def get_docs(directory):
	docs = set()
	for root, subFolders, files in os.walk(directory):
		for file1 in files:
			filePath = root + "/" + file1
			#print filePath
			docs.add(filePath)
	return docs

my_docs = get_docs("Reuters/test")
def clean_index(dirname, index_type):
	# Always create the index from scratch
	ix = index.create_in(dirname, my_schema)
	writer = ix.writer()

	# Assume we have a function that gathers the filenames of the
	# documents to be indexed
	for path in my_docs:
		add_doc(writer, path, index_type)

 	writer.commit()

def get_tags(content, index_type):
	tag_set = set()
	tag_string = ""
	# reduce string to bare letters
	no_punc = content.translate(translate_tab, string.punctuation)
	doc = re.split(" |\n", no_punc)

	if index_type == "Unstemmed":
		for each_word in doc:
			word = each_word.lower()
			if word not in stopset:
				tag_set.add(word)
				tag_string = tag_string + " " + word

	elif index_type == "Porter":

		for each_word in doc:
			word = each_word.lower()
			if word not in stopset:
				word = p_s.stem(word)
				tag_set.add(word)
				tag_string = tag_string + " " + word

	elif index_type == "Snowball":
		for each_word in doc:
			word = each_word.lower()
			if word not in stopset:
				word = s_s.stem(word)
				tag_set.add(word)
				tag_string = tag_string + " " + word 

	elif "kgram" in index_type:
		if "4" in index_type:
			kgram_number = 4
		else: 
			kgram_number = 5

		for each_word in doc:
			full_word = each_word.lower()
			if full_word not in stopset:
				k = len(full_word) - kgram_number
				for i in range(0, k + 1):
					word = full_word[i:i+kgram_number]

					tag_set.add(word)
					tag_string = tag_string + " " + word

	return tag_set, tag_string

def add_doc(writer, path, index_type):
	fileobj = open(path, "r")
	content = fileobj.read()
	fileobj.close()
	stripped, title = strip_content(content)
	tag_set, tag_string = get_tags(stripped, index_type)
	try:
		writer.add_document(docId=unicode(path), title=unicode(title), tags=unicode(tag_string), body=unicode(stripped))
	except:
		print("failed")
		pass

index_types = ["Unstemmed", "Porter", "Snowball", "kgram4", "kgram5"]
for index_type in index_types:
	clean_index("indices/" + index_type + "_Index", index_type)