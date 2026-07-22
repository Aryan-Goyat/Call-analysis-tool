# IT Analytics Dashboard

A web-based dashboard for visualizing and analyzing IT service desk data, including Change Requests (CRs), Service Requests (SRs), and Incidents. 

Built with Plotly Dash and Flask, the tool includes custom authentication, interactive charts, and AI-powered insights via the Groq API.

## Features
- **Data Visualization**: Interactive reports for CRs, SRs, and Incidents.
- **AI Insights**: Integrates with Groq to summarize and analyze ticket data.
- **Custom Authentication**: Built-in login and password reset flows with rate limiting.
- **Email Notifications**: Automated email service for user management.

## Tech Stack
- **Frontend/Backend**: Python, Dash, Flask
- **Database**: SQLAlchemy, PyMySQL
- **AI**: Groq API
- **Styling**: Dash Bootstrap Components, Custom CSS

## Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   cd Call-Analysis-Tool
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the `Frontend` directory with your configuration:
   ```env
   API_KEY=your_groq_api_key
   SECRET_KEY=your_flask_secret_key
   # Add your database connection string and email config here
   ```

4. Run the application:
   ```bash
   python Frontend/main.py
   ```

The dashboard will be available at `http://127.0.0.1:8050/`.