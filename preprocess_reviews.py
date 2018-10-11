import os, json, sys, langdetect, collections, spacy, pandas, re, liwc, readline, unidecode

"""This script does a full cleaning of the reviews and stores the newly cleaned versions in a single Pandas DataFrame for each book.

Here are the steps of the cleaning
I)		detect the language and only include those reviews that are in English (langdetect)
II)		remove apostrophes (Spacy's tokenization does not)
III)	resolve coreferences (spaCy)
IV)	   stoplists on the basic spaCy stoplist. (spaCy)
V)	   replaces tokens with their lemmas. (spaCy)
VI)    remove all unique words
VII)   remove documents with less than 10 words.

 I remove low word count documents because I've observed short "reviews" on this site to be expressions of approval/disapproval and lacking in expressions of (perceived) meaning (e.g. "I read this on vacation and loved it"). Finally, I did not stoplist on collection-specific high frequency words because I will vary the threshold later and don't want to have to rerun this cleaning process each time.

While I am very much in favor of resolving coreferences, it will likely under-perform here because I long ago removed punctuation and I assume it is harder to do coreference resolution without it. In testing, it does catch a good number, however.

The newly cleaned reviews are stored as individual records in a single Pandas dataframe. Other fields in the dataframe include the delta (i.e. posting date relative to the book's publication date), the user's rating of the book, the number of "up-votes" the review received, and the raw text string.
"""
CATS = ['affect', 'posemo', 'negemo','anx', 'anger', 'sad']

def remove_repeat(string,threshold):
	test = True
	i = 0

	try:
		if len(string) >0:
			while test:
				start = string[:i]
				results = re.search(start,string[i:])
				if results != None:
					i += 1
				else:
					test = False

		if i < threshold:
			return(string)
		else:
			if string[-5:]==" more":
				return string[i-1:-5] # removing a "more" on the end of the long paragraphs
			else:
				if string[:i].strip() == string[i:].strip():
					print("weird corner:", string)
					print("returned",string[:i])
					return string[:i]
				else:
					a = t
	except:
			print(i, threshold)
			correct_input = input("What should this review be?  {}:   ".format(string))
			return correct_input

def liwc_parse(sentence):
	counts = liwc.from_tokens(sentence)
	reordered = {}
	for j in CATS:
		try:
			reordered[j] = round(counts[j],4)
		except:
			reordered[j] = 0

	return reordered

nlp = spacy.load('en_coref_lg') # Using the large (coreference) model

nlp.Defaults.stop_words |= {".","!","?",";",":",",","/","\"","&",'-',"--","\n","&amp","u0026amp"," ","b","c","d", "e","f","g","h", "j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"}
# OK, we iterate over all the books.
for directory, sub, files in os.walk("../../posts/"):
	book_dir = directory.split("/")[-1] #Book id+name
	# In case the script stops with an error, we make sure the current book hasn't already been done
	if not os.path.exists("./cleaned_posts/"+book_dir+".json"): # should have not after if.

		print("cleaning {}".format(book_dir))

		records = []
		for file in files:

			if ".json" in file: # Some times there are ".DS_Store" and other files in the folder
				with open(directory+"/"+file, "r",encoding="ascii") as f:
					book_dictionary = json.loads(f.read()) # records are stored in the JSON format
					temp = " ".join(book_dictionary["doc"]) # the reviews are already tokenized.
					try:
						review = remove_repeat(unidecode.unidecode(temp),25)
					except:
						print(review)
						raise ValueError("some value error")
					try:
						# we only continue with the processing if the text is in English.
						if langdetect.detect(review) == "en":

							record = dict(book_dictionary)
							#  We remove the apostrophes before parsing the text with replace
							doc = nlp(review.replace("'s","").replace("'","")) # nlp runs all of Spacy's tokenizing/coref-res/etc.

							#It has now done the coreference resolution, but those new tokens don't have lemmas attached, so we have to insert them and run it again
							if doc._.has_coref:
								coref_doc = nlp(doc._.coref_resolved) # re-running spaCy's parsing process with the coreferences inserted
							else:
								coref_doc = doc

							# Now we have the resolved and lemmatized text and we can stoplist it
							stoplisted = []
							removed_words = []
							for token in coref_doc:
								if token.text not in nlp.Defaults.stop_words:
									stoplisted.append(token)
								else:
									removed_words.append(token.text)
							removed_words = list(set(removed_words))


							# The above stoplists on token.text because the token itself doesn't evaluate to the actual word. We save the token because the lemma is attached to the token and we need the lemmas next.

							resolved_doc = [token.lemma_  if token.lemma_ != "-PRON-" else token.text for token in stoplisted]

							# putting in the lemmas, except for pronoun because they don't really have lemmas

							#We now have the bag of words we want and we can pack the data up again

							record["doc"] = resolved_doc
							record["removed_words"] = removed_words
							record["name"] = file
							record['raw_text'] = review
							parsed= liwc_parse(resolved_doc)
							record.update(parsed)
							records.append(record)

					except:
						try:
							# Goodreads has a convention where users who want to assign a 1/2 star in a rating do this in the text field (e.g. 3.5). Just this text confuses langdetect so we catch it here. (If the post has other text, it's fine). A single emoji will confuse it too.
							print("langdetect doesn't like:", review)
							print("it was tossed")
						except:
							#Print can't print emojis or other ASCII characters.
							print("langdetect doesn't like an emoji or something")

		# Counting the words in the collection
		counts = collections.Counter()
		for review in [d["doc"] for d in records]:
			for word in review:
				counts[word] += 1

		# From the counts, we get the words that occured a single time.
		isolates = []
		for word, count in counts.items():
			if count == 1:
				isolates.append(word)

		frames = {}
		index = 1
		# Now we remove the isolated words and pack the data up for storage.
		for record in records:
			text = record["doc"]
			iso_stopped = []
			stop_listed_text = []
			for word in text:
				if word not in isolates:
					stop_listed_text.append(word)
				else:
					iso_stopped.append(word)
			if type(record["ups"]) == int:
				likes = record["ups"]
			else:
				likes = int(record["ups"].replace(" likes","").replace(" like",""))

			record["removed_words"].extend(iso_stopped)
			new_data = {
							"doc": stop_listed_text,
							"word_count": len(stop_listed_text),
							"ups": likes
							}
			record.update(new_data)

			frames[index] = pandas.Series(record)
			index += 1

		master_frame = pandas.DataFrame(frames)

		with open("./cleaned_posts/"+book_dir+".json","w") as fprime:
			fprime.write(master_frame.T.to_json())
