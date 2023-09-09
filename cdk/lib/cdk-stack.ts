import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'
import * as lambda from 'aws-cdk-lib/aws-lambda'

export class CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const tableName = "dropbox2slack-table"
    const lambdaFunctionName = "dropbox2slack"

    const table = new dynamodb.Table(this, tableName, {
      tableName: tableName,
      partitionKey: {
        name: "id",
        type: dynamodb.AttributeType.STRING,
      },
    })

    const lambdaFunction = new lambda.Function(this, lambdaFunctionName, {
      code: new lambda.AssetCode("../lambda/src"),
      handler: "lambda_function.lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_9,
      environment: {
        "TABLE_NAME": tableName,
      }
    })
  }
}
