# Mindful Content

## Description
**Mindful Content** is a tool designed to help you become more aware of the audiovisual content you consume. We understand that movies and series can influence our perceptions and beliefs. That's why, using artificial intelligence models, we analyze and evaluate whether these works reinforce negative roles in society. We aim to support you in choosing content that is enriching and positive.

## Features
- **TMDB API**: Retrieve detailed information about movies and series directly from the TMDB database.
- **Bias Analysis**: Run multiple tests to identify and evaluate potential biases in the content.
- **Clear Results**: Provide a simple report on whether the content passes the tests, accompanied by a brief description.
- **Summary and Rating**: Generate a summary paragraph and a score to give you an overall view of the analyzed content.

## Installation
To install and run the project locally:

1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/mindful-content.git
    ```
2. Navigate to the project directory:
    ```sh
    cd mindful-content
    ```
3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Use

### Interactive Mode
Run the application:
```sh
cd private
streamlit run Home.py
```

### Batch Mode
```sh
python analyzer.py
```

Command Line Options

* `--year`: Year of movies to analyze
* `--page`: Page number for API request (default: 1)
* `--overwrite`: Overwrite data for existing movies (default: False)
* `--clear-cache`: Clear cache before analysis (default: False)
* `--remote-llm`: Use remote model like OpenAI(default: True)
* `--movie-id`: ID of movie to analyze (optional)

## Contributing

Contributions are welcome! If you want to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/new-feature`).
3. Make the necessary changes and commit (`git commit -am 'Add new feature'`).
4. Push the changes to the branch (`git push origin feature/new-feature`).
5. Open a Pull Request.
