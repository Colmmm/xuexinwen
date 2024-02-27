# Xue Xinwen

![Xue Xinwen Logo](public/logo512.png)

Development of a web application named "Xue Xinwen" that fetches and displays news articles.

## Technology Stack

- **Frontend:** Create React App
- **Backend:** Flask
- **News Fetcher:** Custom script
- **Reverse Proxy:** Nginx
- **Containerization:** Docker

## Docker Compose Setup

Three services: frontend, backend, and news_fetcher.
Nginx used as a reverse proxy for serving the React app.
Docker Compose manages builds, images, ports, volumes, and environment variables.

## Nginx Configuration

Nginx configured to handle routing and serve the React app.
Two configurations for development and production environments.

## React App Development

Utilizing Create React App for frontend development.
Dockerized React app with specific environment variables for production.


## Getting Started

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/your-username/xue-xinwen.git
    cd xue-xinwen
    ```

2. **Install Docker and Docker Compose:**

    ```bash
    sudo apt install docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo apt install docker-compose
    ```

3. **Set OPENAI API Key:**

    Remember to set your OPENAI API key in your bashrc or another suitable location.

4. **Build Docker Images:**

    Make sure to set your OPENAI API key before running the next command.

    ```bash
    docker-compose build
    ```

5. **Adjust Permissions:**

    Add your user to the docker group and adjust permissions:

    ```bash
    sudo usermod -aG docker $USER
    sudo chown $USER:docker /var/run/docker.sock
    ```

6. **Start the Application:**

    ```bash
    docker-compose up
    ```

7. **Open in Browser:**

    Open your browser and navigate to [http://localhost:3000](http://localhost:3000).

---

**Note:** Ensure that the necessary environment variables are set for the application to function correctly. Regularly update the documentation with any changes or improvements made during development and deployment.


## License

This project is licensed under the [MIT License](LICENSE).