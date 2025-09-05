// Simple trigger Jenkinsfile for application repository
// This triggers the main CI/CD pipeline when code changes are pushed

pipeline {
    agent any
    
    triggers {
        githubPush()
    }
    
    stages {
        stage('Trigger Deployment Pipeline') {
            steps {
                echo '🚀 Code change detected - triggering deployment pipeline'
                
                // Trigger the main infrastructure pipeline
                build job: 'qr-checkin-infrastructure-pipeline',
                      wait: false,
                      parameters: [
                          string(name: 'APP_BRANCH', value: env.BRANCH_NAME),
                          string(name: 'COMMIT_SHA', value: env.GIT_COMMIT),
                          booleanParam(name: 'FORCE_REBUILD', value: true)
                      ]
            }
        }
    }
    
    post {
        success {
            echo '✅ Successfully triggered deployment pipeline'
        }
        failure {
            echo '❌ Failed to trigger deployment pipeline'
        }
    }
}