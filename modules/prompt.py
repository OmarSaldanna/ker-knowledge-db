

# context is what db found
# question what the user wants
# and config is the db config
def create_prompt (context, question, config):
	# use the prompt from the config
	prompt = "\n".join(config["prompt"])
	# insert the user question
	prompt = prompt.replace("{*question}", question)
	# 
	context_str = ""
	for c in context:
		context_str += "\n"
		context_str += c["content"]
		context_str += "\n"
		# if the content has pages (comes from a pdf, pptx or docx)
		if "pages" in c:
			context_str += "Páginas: " + str(c["pages"]) + ". "
		context_str += "Fuente: " + c["source"]
		context_str += "\n"
	# and the context from the db
	prompt = prompt.replace("{*context}", context_str)
	return prompt