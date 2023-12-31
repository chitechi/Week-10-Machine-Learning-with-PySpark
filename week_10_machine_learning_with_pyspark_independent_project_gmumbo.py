# -*- coding: utf-8 -*-
"""Week 10: Machine Learning with PySpark - Independent Project_GMumbo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gD-922Fm9ih0akiQAYxF7LzVcCeTFgoz
"""

!pip install pyspark

#Import the necesary libraries
from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier, LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

# Initialize SparkSession
spark = SparkSession.builder.appName("TelecomChurnPrediction").getOrCreate()

# Load the CSV file into a DataFrame
df = spark.read.csv("telecom_dataset.csv", header=True, inferSchema=True)

# Handling missing values
df = df.dropna()

# Encoding categorical variables
indexers = [StringIndexer(inputCol=col, outputCol=col + "_index").fit(df) for col in ['Gender', 'Contract', 'Churn']]
pipeline = Pipeline(stages=indexers)
df = pipeline.fit(df).transform(df)

# Splitting the data into training and testing sets
train_data, test_data = df.randomSplit([0.7, 0.3], seed=42)

# Feature columns
feature_cols = ['Gender_index', 'Age', 'Contract_index', 'MonthlyCharges', 'TotalCharges']

# Assembling the features into a vector
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")

# Define the models to try
models = [
    RandomForestClassifier(labelCol="Churn_index", featuresCol="features", seed=42),
    LogisticRegression(labelCol="Churn_index", featuresCol="features")
]

# Create a list of parameter grids to search through
paramGrids = [
    ParamGridBuilder().addGrid(RandomForestClassifier.maxDepth, [5, 10]).build(),
    ParamGridBuilder().addGrid(LogisticRegression.regParam, [0.01, 0.1]).build()
]

# Create a list to store the accuracy for each model
accuracies = []

# Train and evaluate each model
for i, model in enumerate(models):
    pipeline = Pipeline(stages=[assembler, model])

    # Set up the cross-validator
    crossval = CrossValidator(estimator=pipeline,
                              estimatorParamMaps=paramGrids[i],
                              evaluator=BinaryClassificationEvaluator(labelCol="Churn_index"),
                              numFolds=5)

    # Fit the model and select the best set of parameters
    cvModel = crossval.fit(train_data)
    bestModel = cvModel.bestModel

    # Make predictions on the test data
    predictions = bestModel.transform(test_data)

    # Evaluate the model
    evaluator = BinaryClassificationEvaluator(labelCol="Churn_index")
    accuracy = evaluator.evaluate(predictions)
    accuracies.append(accuracy)

    # Print the accuracy for each model
    print(f"Accuracy for Model {i + 1}: {accuracy}")

# Select the best model based on accuracy
best_model_index = accuracies.index(max(accuracies))
best_model = models[best_model_index]

# Train the best model on the full training data
pipeline = Pipeline(stages=[assembler, best_model])
model = pipeline.fit(df)

# Save the best model
model.save("telecom_churn_model_refined")

# Closing the SparkSession
spark.stop()