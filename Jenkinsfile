pipeline {
    agent any

    environment {
        BRANCH_NAME = "${env.BRANCH_NAME ?: 'bhagavan_aignite'}"
    }

    triggers {
        // Automatically trigger builds on push or PR updates
        pollSCM('* * * * *')
    }

    stages {
        stage('Clone Repository') {
            steps {
                echo "Cloning branch: ${BRANCH_NAME}"
                git branch: "${BRANCH_NAME}", url: 'https://github.com/bhagavansprasad/aignite.git'
            }
        }

        stage('Checkout Branch') {
            steps {
                script {
                    sh 'git checkout ${BRANCH_NAME}'
                    sh 'git pull origin ${BRANCH_NAME}'
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
                    // sh 'source venv/bin/activate && pip install --upgrade pip'
                    sh 'bash -c "source venv/bin/activate && echo Virtualenv Activated"'
                    // sh 'source venv/bin/activate && pip install -r requirements.txt'
                    sh 'bash -c "source venv/bin/activate && pip install -r requirements.txt"'
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    sh 'bash -c "source venv/bin/activate && make utest"'
                }
            }
        }

        stage('Cleanup') {
            steps {
                script {
                    sh 'bash -c "deactivate" || echo "Virtual environment already deactivated"'
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
