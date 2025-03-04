pipeline {
    agent any

    environment {
        VENV_DIR = 'venv'
    }

    stages {
        stage('Clone Repository') {
            steps {
                echo "Cloning the repository..."
                git branch: 'bhagavan_aignite', url: 'https://github.com/bhagavansprasad/aignite.git'
            }
        }

        stage('Checkout Branch') {
            steps {
                script {
                    sh 'git checkout bhagavan_aignite'
                    sh 'git pull origin bhagavan_aignite'
                }
            }
        }

        stage('Clean and Setup Virtual Environment') {
            steps {
                script {
                    sh 'make clean'
                    sh 'rm -rf venv'
                    sh 'python3 --version'
                    sh 'python3 -m venv venv'
                    sh 'ls -l venv'
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    sh '. venv/bin/activate && pip install --upgrade pip'
                    sh '. venv/bin/activate && pip install -r requirements.txt'
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    sh '. venv/bin/activate && make utest'
                }
            }
        }

        stage('Cleanup') {
            steps {
                script {
                    sh 'if [ -f venv/bin/activate ]; then . venv/bin/activate && deactivate; fi'
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline execution completed!"
        }
    }
}
