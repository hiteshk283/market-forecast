pipeline {
    agent any

    environment {
        DOCKER_REPO = "hiteshk283/forecast"
        IMAGE_TAG   = "${BUILD_NUMBER}"
        FULL_IMAGE  = "${DOCKER_REPO}:${IMAGE_TAG}"
        GIT_BRANCH  = "main"
    }

    stages {

        stage('Checkout Application Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                docker build -t ${FULL_IMAGE} .
                """
            }
        }

        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                    echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin
                    """
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                sh """
                docker push ${FULL_IMAGE}
                """
            }
        }

        stage('Update K8s Manifests (GitOps)') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-creds',
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_PASS'
                )]) {
                    dir('gitops') {
        
                        git branch: "main",
                            credentialsId: 'github-creds',
                            url: 'https://github.com/hiteshk283/market-forecast.git'
        
                        sh """
                        cd k8s
        
                        echo "Updating image to ${FULL_IMAGE}"
        
                        for file in *.yaml; do
                            sed -i "s|image:.*forecast:.*|image: ${FULL_IMAGE}|g" \$file
                        done
        
                        git config user.email "jenkins@ci.com"
                        git config user.name "jenkins"
        
                        git add .
                        git commit -m "Update image to ${IMAGE_TAG}" || echo "No changes to commit"
        
                        git remote set-url origin https://${GIT_USER}:${GIT_PASS}@github.com/hiteshk283/market-forecast.git
                        git push origin HEAD:main
                        """
                    }
                }
            }
        }



    }

    post {
        success {
            echo "✅ Docker image pushed successfully."
            echo "🚀 Git updated. ArgoCD will auto-sync."
        }
        failure {
            echo "❌ Pipeline failed."
        }
    }
}
