pipeline {
    agent any

    environment {
        BRANCH_NAME = "${env.BRANCH_NAME ?: 'bhagavan_aignite'}"
        GIT_COMMIT_HASH = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
        GITHUB_TOKEN = credentials('NewGitHubTokenPublishResults')
        GITHUB_REPO = 'bhagavansprasad/aignite' 
    }

    triggers {
        pollSCM('* * * * *')
    }

    stages {
        stage('Set Build Status: Pending') {
            steps {
                script {
                    updateGitHubStatus('pending', "Build started...")
                }
            }
        }

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
                    sh 'bash -c "source venv/bin/activate && echo Virtualenv Activated"'
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

        stage('Set Build Status: Success') {
            when {
                expression { currentBuild.resultIsBetterOrEqualTo('SUCCESS') }
            }
            steps {
                script {
                    updateGitHubStatus('success', "Build completed successfully!")
                }
            }
        }
    }

    post {
        failure {
            script {
                updateGitHubStatus('failure', "Build failed! Check logs.")
            }
        }
        always {
            echo "Pipeline execution completed!"
        }
    }
}

// Function to update GitHub commit status
def updateGitHubStatus(String state, String description) {
    sh """
        curl -X POST -H "Authorization: token ${GITHUB_TOKEN}" -H "Accept: application/vnd.github.v3+json" \
        https://api.github.com/repos/${GITHUB_REPO}/statuses/${GIT_COMMIT_HASH} \
        -d '{
            "state": "${state}",
            "description": "${description}",
            "context": "Jenkins CI/CD",
            "target_url": "${env.BUILD_URL}"
        }'
    """
}
