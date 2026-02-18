pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "host.docker.internal:5000/market-forecast"
        NAMESPACE = "market-forecast"
        DEPLOYMENT = "nifty"
        TRAIN_CRON = "nifty-train-job"
        UPDATE_CRON = "nifty-update-job"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .
                """
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                    docker logout
                    """
                }
            }
        }

        stage('Update Kubernetes Deployment') {
            steps {
                sh """
                kubectl set image deployment/${DEPLOYMENT} \
                ${DEPLOYMENT}=${DOCKER_IMAGE}:${IMAGE_TAG} \
                -n ${NAMESPACE}
                """
            }
        }

        stage('Update Kubernetes CronJobs') {
            steps {
                sh """
                kubectl set image cronjob/${TRAIN_CRON} \
                ${TRAIN_CRON}=${DOCKER_IMAGE}:${IMAGE_TAG} \
                -n ${NAMESPACE}

                kubectl set image cronjob/${UPDATE_CRON} \
                ${UPDATE_CRON}=${DOCKER_IMAGE}:${IMAGE_TAG} \
                -n ${NAMESPACE}
                """
            }
        }

        stage('Verify Rollout') {
            steps {
                sh """
                kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE}
                """
            }
        }
		
		stage('Cleanup Old Registry Images') {
            steps {
                script {
                    sh '''
                    REPO="market-forecast"
                    REGISTRY="http://host.docker.internal:5000"
	        
                    # Get all tags
                    TAGS=$(curl -s $REGISTRY/v2/$REPO/tags/list | jq -r '.tags[]' | sort -n)
	        
                    # Count tags
                    COUNT=$(echo "$TAGS" | wc -l)
	        
                    if [ "$COUNT" -gt 1 ]; then
                        # Get latest tag
                        LATEST=$(echo "$TAGS" | tail -n 1)
	        
                        echo "Latest tag: $LATEST"
	        
                        # Delete all except latest
                        for TAG in $TAGS; do
                            if [ "$TAG" != "$LATEST" ]; then
                                echo "Deleting tag: $TAG"
	        
                                DIGEST=$(curl -sI -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
                                $REGISTRY/v2/$REPO/manifests/$TAG | \
                                grep Docker-Content-Digest | awk '{print $2}' | tr -d '\\r')
	        
                                curl -X DELETE $REGISTRY/v2/$REPO/manifests/$DIGEST
                            fi
                        done
                    else
                        echo "Only one image present. No cleanup needed."
                    fi
                    '''
               }
            }
        }

    }

    post {
        success {
            echo "Deployment successful 🚀 Image tag: ${IMAGE_TAG}"
        }
        failure {
            echo "Build or Deployment Failed ❌"
        }
    }
}
