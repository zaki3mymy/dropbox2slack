import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as apigateway from 'aws-cdk-lib/aws-apigateway'
import { RemovalPolicy } from 'aws-cdk-lib';

export class CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const prefix = ""

    const appName = `${prefix}dropbox2slack`
    const tableName = `${appName}-table`
    const lambdaFunctionName = `${appName}`
    const lambdaLayerName = `${appName}-layer`
    const restApiName = `${appName}-api`

    const table = new dynamodb.Table(this, tableName, {
      tableName: tableName,
      partitionKey: {
        name: "id",
        type: dynamodb.AttributeType.STRING,
      },
      removalPolicy: RemovalPolicy.DESTROY,
    })

    const lambdaLayer = new lambda.LayerVersion(this, lambdaLayerName, {
      layerVersionName: lambdaLayerName,
      code: new lambda.AssetCode("../layer"),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_9],
    })

    const lambdaFunction = new lambda.Function(this, lambdaFunctionName, {
      functionName: lambdaFunctionName,
      code: new lambda.AssetCode("../src/dropbox2slack"),
      handler: "lambda_function.lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_9,
      environment: {
        "TABLE_NAME": tableName,
        "DROPBOX_TOKEN": "PUT_YOUR_TOKEN",
        "DROPBOX_TARGET_DIR": "/path/to/dir",
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/xxxxxxxx"
      },
      layers: [lambdaLayer],
    })

    const restApi = new apigateway.RestApi(this, restApiName, {
      restApiName: restApiName,
      deployOptions: {
        stageName: "v1",
      }
    })
    restApi.root.addMethod("GET", new apigateway.LambdaIntegration(lambdaFunction))
    restApi.root.addMethod("POST", new apigateway.LambdaIntegration(lambdaFunction))
  }
}
