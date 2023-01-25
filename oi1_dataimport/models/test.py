import re

def main():
	value = "Postadres :  Aelbrechtskolk 47 3025 HB ROTTERDAM NEDERLAND Bezoekadres :  Aelbrechtskolk 47 3025 HB ROTTERDAM NEDERLAND"


	value = value.replace("Postadres :","")
	value = value.replace("Bezoekadres", "")
	value = value.split(":")

	post = value[0]

	pattern = "\d\d\d\d\s\w\w"


	postcomponents = re.findall(pattern, post)
	print(postcomponents)

if __name__ == "__main__":
	main()