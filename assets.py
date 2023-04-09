"""
This module contains the base class for all game assets and image processing.
"""
import io
import os
from pathlib import Path

import emoji
import requests
from bs4 import BeautifulSoup
from PyDictionary import PyDictionary


class GameAsset:
    """
    GameAsset is the base class for all game assets.
    """

    def __init__(self, size=50):
        self.emoji = "💩"
        self.path_to_image = None
        self.size = size
        self.image_directory = "images"
        self.url_for_emoji = None
        self.base_url = "https://emojipedia.org"
        self.query = self.__str__().lower()
        self.image_name = None
        self.image_path = None

    def process_image(self):
        """
        This method checks the if the directory for the image exists and if the image exists.
        If the directory does not exist, it is created.
        If the image does not exist, it is created.
        :return:
        """
        if not os.path.exists(self.image_directory):
            os.makedirs(self.image_directory)
        self.path_to_image = os.path.join(self.image_directory, f"{self.__str__()}.png")
        if not os.path.exists(self.path_to_image):
            self.create_image()
        # self.create_image()

    def create_image(self):
        """
        This method creates an image from an emoji and saves it to the image directory.
        :return:
        """
        try:
            self.search_openmoji()
        except ValueError:
            print(f"first try failed for {self.__str__()}")
            if other_options := self.try_other_words():
                print(f"Trying other words for {self.__str__()}...")
                for option in other_options:
                    print(f"Trying {option}...")
                    try:
                        self.search_openmoji(query=option)
                    except ValueError:
                        print(f"Could not find an image for {option}...")
                        continue
                    if self.url_for_emoji:
                        print(f"Found an emoji for {option}!")
                        if self.download_image():
                            return
                        else:
                            continue
        if self.url_for_emoji:
            print(f"Saving an emoji image for {self.__str__()}...")
            self.download_image()
        if not self.url_for_emoji:
            manual_search_success = False
            while not manual_search_success:
                manual_search_success = self.manual_search()
                if manual_search_success and self.url_for_emoji:
                    download_success = self.download_image()
                    if not download_success:
                        manual_search_success = False
                        continue
                still_searching = input(
                    "Do you want to search for another emoji? (y/n)"
                )
                if still_searching.lower() != "y":
                    return
                self.url_for_emoji = None
                manual_search_success = False

            return

    def search_openmoji(self, query=None):
        """
        This function searches for an emoji on the openmoji website and downloads the image.
        :return:
        """
        # first check if the file already exists
        self.image_name = f"{self.__str__()}.png"
        self.image_path = os.path.join("images", self.image_name)
        if os.path.exists(self.image_path):
            print("Image already exists")
            return
        query = query.lower() if query else self.__str__().lower()
        all_h2s = self.lookup_h2s(query)
        possible_emojis = []
        for h2 in all_h2s:
            if h2.find("a") and query in h2.find("a").text.lower():
                print(h2.find("a").text)
                print(h2.find("a").get("href"))
                possible_emojis.append(h2.find("a").get("href"))
        if not possible_emojis:
            raise ValueError("No emoji found")
        if len(possible_emojis) == 1:
            print("Found one emoji!")
            self.url_for_emoji = f"{self.base_url}{possible_emojis[0]}"
        else:
            shortest = min(possible_emojis, key=len)
            print(f"Found multiple emojis! Choosing the shortest one: {shortest}")
            self.url_for_emoji = f"{self.base_url}{shortest}"

    def download_image(self):
        """
        This function downloads the image from the url_for_emoji attribute.
        :return:
        """
        response = requests.get(self.url_for_emoji)
        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}")
            return
        soup = BeautifulSoup(response.text, "html.parser")
        image_download_link = soup.find_all("img")[0]
        # download image and save it
        image_url = image_download_link.get("src")
        # check if the url is valid:
        if not image_url.startswith("https://"):
            image_url = f"{self.base_url}{image_url}"
        image_name = f"{self.__str__()}.png"
        image_path = os.path.join("images", image_name)
        img_request = requests.get(image_url)
        if img_request.status_code != 200:
            print(f"Request failed with status code {img_request.status_code}")
            return
        # show the image if it was found and ask the user if they want to use it
        try:
            image = Image.open(io.BytesIO(img_request.content))
            image.show()
            use_image = input(f"Use this image for {self.__str__()}? (y/n)")
            if use_image.lower() != "y":
                self.url_for_emoji = None
                return False
            if not os.path.exists(image_path):
                with open(image_path, "wb") as f:
                    f.write(requests.get(image_url).content)
                    return True
        except ValueError:
            print("Image could not be opened")
        return False

    def lookup_h2s(self, query):
        """
        This function looks up all h2s on the openmoji website.
        :return:
        """

        search_url = f"{self.base_url}/search/?q={query}"
        response = requests.get(search_url)

        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        return soup.find_all("h2")

    def try_other_words(self):
        """
        This function tries other words if the current word is not found.
        :return:
        """
        print(f"Finding dictionary values for {self.query}...")
        dictionary = PyDictionary(self.query)
        print(f"Getting grammar for {self.query}...")
        grammar = dictionary.getMeanings()
        nouns = grammar[self.query].get("Noun")
        verbs = grammar[self.query].get("Verb")
        adjectives = grammar[self.query].get("Adjective")
        # combine all nouns, verbs and adjectives into one list
        all_words = []
        if nouns:
            all_words.extend(nouns)
            print(f"Found {len(nouns)} nouns for {self.query}.")
        if verbs:
            all_words.extend(verbs)
            print(f"Found {len(verbs)} verbs for {self.query}.")
        if adjectives:
            all_words.extend(adjectives)
            print(f"Found {len(adjectives)} adjectives for {self.query}.")
        # split each index into a list of words
        all_words = [word.split(" ") for word in all_words]
        print(f"Combined all words for {self.query}.")
        # flatten the list
        all_words = [word for sublist in all_words for word in sublist]
        print(f"Found {len(all_words)} words for {self.query}.")
        # remove duplicates
        all_words = list(set(all_words))
        print(f"Removed duplicates for {self.query}.")
        # remove the query
        all_words = [word for word in all_words if word != self.query]
        print(f"Removed any self-references for {self.query}.")
        # remove words that are too short
        all_words = [word for word in all_words if len(word) > 3]
        print(f"Removed words that are too short for {self.query}.")
        return all_words

    def manual_search(self):
        """
        This function allows the user to manually search for an emoji.
        :return:
        """
        print("Could not find an image for this word.")
        manual_prompt = input(
            "Do you want to enter an override value to search for? (y/n)"
        )
        if manual_prompt.lower() == "y":
            manual_query = input("Enter the query to search for: ")
            try:
                self.search_openmoji(query=manual_query)
            except ValueError:
                print("Could not find an image for this query.")
                return
            if self.url_for_emoji:
                print(f"Saving an emoji image for {self.__str__()}...")
                self.download_image()
                return True
            else:
                print("Could not find an image for this query.")
                return False
