pipeline {
  agent {
    label "jenkins-python"
  }
  environment {
    JX_USER_CODEFIX_TOKEN = credentials('cn_jx_user_codefix_token')
    REPO_URL = "${scm.getUserRemoteConfigs()[0].getUrl()}"
    BRANCH = "${env.BRANCH_NAME}"
    COMMIT_ID = "${env.GIT_COMMIT}"
    ORG = 'pzheng64'
    APP_NAME = 'djproject'
    CHARTMUSEUM_CREDS = credentials('jenkins-x-chartmuseum')
  }
  triggers {
    cron(env.BRANCH_NAME == 'master' ? '0 0 * * *': '')
  }
  stages {
    stage('Trigger codefix analysis') {
      when {
        beforeAgent true
        branch 'master'
        expression {
          for (Object currentBuildCause : currentBuild.rawBuild.getCauses()) {
            return currentBuildCause.class.getName().contains('TimerTriggerCause')
          }
        }
      }
      steps {
        container('python') {
          sh "yum install curl"
          sh "curl -X POST \"https://codefix2-prod.public.ey.devfactory.com/api/repo_revisions/\" -H  \"accept: application/json\" -H  \"Content-Type: application/json\" -H \"Cookie: token=$JX_USER_CODEFIX_TOKEN\" -d '[  {    \"scm_url\": \"$REPO_URL\",    \"commit_id\": \"$COMMIT_ID\",    \"branch\": \"$BRANCH\"  }]'"
        }
      }
    }
    stage('CI Build and push snapshot') {
      when {
        branch 'PR-*'
      }
      environment {
        PREVIEW_VERSION = "0.0.0-SNAPSHOT-$BRANCH_NAME-$BUILD_NUMBER"
        PREVIEW_NAMESPACE = "$APP_NAME-$BRANCH_NAME".toLowerCase()
        HELM_RELEASE = "$PREVIEW_NAMESPACE".toLowerCase()
      }
      steps {
        container('python') {
          sh "export VERSION=$PREVIEW_VERSION && skaffold build -f skaffold.yaml"
          sh "jx step post build --image $DOCKER_REGISTRY/$ORG/$APP_NAME:$PREVIEW_VERSION"
          dir('./charts/preview') {
            sh "make preview"
            sh "jx preview --app $APP_NAME --dir ../.."
            sh "kubectl get secret pzheng64-djproject --namespace=jx-preview --export -o yaml | kubectl apply --namespace=jx-$ORG-$PREVIEW_NAMESPACE -f -"
          }
        }
      }
    }
    stage('Build Release') {
      when {
        branch 'master'
      }
      steps {
        container('python') {

          // ensure we're not on a detached head
          sh "git checkout master"
          sh "git config --global credential.helper store"
          sh "jx step git credentials"

          // so we can retrieve the version in later steps
          sh "echo \$(jx-release-version) > VERSION"
          sh "jx step tag --version \$(cat VERSION)"
          sh "export VERSION=`cat VERSION` && skaffold build -f skaffold.yaml"
          sh "jx step post build --image $DOCKER_REGISTRY/$ORG/$APP_NAME:\$(cat VERSION)"
        }
      }
    }
    stage('Promote to Environments') {
      when {
        branch 'master'
      }
      steps {
        container('python') {
          dir('./charts/djproject') {
            sh "jx step changelog --version v\$(cat ../../VERSION)"

            // release the helm chart
            sh "jx step helm release"

            // promote through all 'Auto' promotion Environments
            sh "jx promote -b --all-auto --timeout 1h --version \$(cat ../../VERSION)"
          }
        }
      }
    }
  }
  post {
        always {
          cleanWs()
        }
  }
}
