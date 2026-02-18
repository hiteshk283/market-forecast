pipeline {
    agent any

    environment {
        DOCKER_REPO = "hiteshk283/forecast"
        IMAGE_TAG   = "${BUILD_NUMBER}"
        FULL_IMAGE  = "${DOCKER_REPO}:${IMAGE_TAG}"
        GIT_URL     = "https://github.com/hiteshk283/market-forecast.git"
        K8S_PATH    = "k8s"
    }

    stages {

        stage('Checkout Source Code') {
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

        stage('Update Kubernetes Manifests (GitOps)') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-creds',
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_PASS'
                )]) {
                    sh """
                    rm -rf gitops

                    git clone https://${GIT_USER}:${GIT_PASS}@github.com/hiteshk283/market-forecast.git gitops

                    cd gitops/${K8S_PATH}

                    echo "Updating image to ${FULL_IMAGE}"

                    # Update only our Docker image across all YAML files
                    for file in *.yaml; do
                        sed -i "s|image: ${DOCKER_REPO}:.*|image: ${FULL_IMAGE}|g" \$file
                    done

                    git config user.email "jenkins@ci.com"
                    git config user.name "jenkins"

                    git add .
                    git commit -m "Update image to ${IMAGE_TAG}"
                    git push
                    """
                }
            }
        }
    }

    post {
        success {
            echo "✅ Image built, pushed, and Git updated successfully."
            echo "🚀 ArgoCD will now auto-sync and deploy."
        }
        failure {
            echo "❌ Pipeline failed."
        }
    }
}
