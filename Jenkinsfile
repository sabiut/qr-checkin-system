// CI/CD Pipeline for QR Check-in System
// This file should trigger when code is pushed to GitHub

pipeline {
    agent any
    
    environment {
        // Server Configuration
        SERVER_IP = '172.105.189.124'
        SSH_KEY_ID = 'linode-ssh-key'
        
        // Repository Configuration  
        APP_REPO = 'https://github.com/sabiut/qr-checkin-system.git'
        INFRA_REPO = 'https://github.com/sabiut/qr-checkin-infrastructure.git'
    }
    
    triggers {
        // This should trigger on GitHub webhook
        githubPush()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📦 Checking out application code...'
                checkout scm
            }
        }
        
        stage('Test Connection') {
            steps {
                echo '🔌 Testing server connection...'
                script {
                    withCredentials([sshUserPrivateKey(
                        credentialsId: "${SSH_KEY_ID}",
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )]) {
                        sh """
                            ssh -i \${SSH_KEY} -o StrictHostKeyChecking=no \${SSH_USER}@${SERVER_IP} '
                                echo "✅ Successfully connected to server"
                                hostname
                                docker --version
                                docker-compose --version
                                pwd
                            '
                        """
                    }
                }
            }
        }
        
        stage('Build') {
            steps {
                echo '🔨 Building application...'
                sh '''
                    echo "Would build Docker images here"
                    echo "Branch: ${BRANCH_NAME}"
                    echo "Commit: ${GIT_COMMIT}"
                '''
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo '🚀 Deploying to production...'
                echo 'Deployment will happen here'
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed!'
        }
        always {
            echo "🏁 Pipeline finished for commit: ${env.GIT_COMMIT}"
        }
    }
}