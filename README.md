# CryoSens Analytics

**Generic analysis framework for industrial thermal sensor data**

CryoSens Analytics is an internal notebook-based toolbox designed to analyze industrial sensor data, especially temperature, pressure, and differential pressure signals.

It was created as a **generic framework** to help detect **rapid variations** that may contribute to material degradation, thermal fatigue, or other damage mechanisms. The tool is also intended to support diagnosis and make sensor data analysis easier and more accessible for internal teams.

## Purpose

The main objective of CryoSens Analytics is to help users:

- load raw sensor data,
- prepare and organize the signals,
- visualize measurements,
- detect abrupt variations,
- support diagnostic work on thermal equipment.

The project is built with a strong focus on **simplicity**, **ease of use**, and **guided analysis**.

## Main Use Case

The primary analysis approach implemented in the generic workflow is **ROC** (*Rate of Change*).

This method focuses on how fast a signal changes over time, rather than only on the signal value itself. It is especially useful for identifying:

- rapid temperature rises,
- sudden drops,
- abnormal transient behavior,
- events that may be relevant for thermal fatigue or material stress.

A complementary cycle analysis module is also available for cases where the process follows a repetitive heating/cooling pattern.

## Target Users

This project is intended for **internal teams** working with industrial sensor data and diagnostic analysis.

The standard workflow is designed to be easy to use, including for users who do not want to interact directly with the source code.

## Supported Data

CryoSens Analytics is designed for time-series sensor data such as:

- temperature data,
- pressure data,
- differential pressure data.

Typical input formats:

- CSV
- Excel

More generally, the framework can be useful for many datasets coming from thermal or process-related sensors.

## Main Entry Point

The main entry point of the project is:

```text
main.ipynb