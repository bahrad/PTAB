# PTAB
Analysis and Outcome Prediction for US Patent & Trademark Office (PTO) Patent Trial and Appeals Board proceedings and decisions.

## PTAB_download_briefs.py
Software code used to download briefs and written decisions from the PTO OpenData website. API documentation: https://developer.uspto.gov/api-catalog/ptab-api-v2 (access PTAB data online at https://developer.uspto.gov/ptab-web/)

## PTAB_Institution_Proceedings_to_20211231.tsv
Raw data for text documents (including Petitions, Written Decisions, Preliminary Response briefs) for Institution phase of IPR, CBM, and PGR post-grant patent review challenges before PTAB. Includes case names and outcomes.

## PTAB_Model_Responses_github.ipynb
Neural network (CNN+Attention) model for Patent Owner Preliminary Response Briefs.

## PTAB_Model_Decisions_github.ipynb
Neural network (CNN+Attention) model for Written Institution Decisions.

## PTAB_xgboost_github.ipynb
XGBoost with TF-IDF for analyzing written decisions and preliminary patent owenr's response briefs.
