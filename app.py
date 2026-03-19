import streamlit as st
import pandas as pd
import openai
from function import (
    load_template_sheets,
    process_description,
    validate_attributes,
    mandatory_attributes_validation_with_llm,
    NormBased_Attribute_Recovery,
)
openai.api_key = st.secrets["OPENAI_API_KEY"]
st.title("🔍 Product Type Identifier & Validator")

st.markdown("This system intelligently analyzes product descriptions to identify the product type and extract all relevant attributes in a structured format.\nIt further validates the extracted data against standard templates and applies intelligent rules to ensure completeness and accuracy.")

uploaded_file = st.file_uploader("Upload Excel File with Pipe, Flange Templates and Norm Sheet", type=["xlsx"])

if uploaded_file:
    pipe_template, flange_template = load_template_sheets(uploaded_file)

    try:
        norm_template = pd.read_excel(uploaded_file, sheet_name="Norm-Std-pipe", header=None)
    except Exception:
        norm_template = None

    description = st.text_area("Enter product description")

    if st.button("Extract and Validate"):
        with st.spinner("Processing..."):
            extracted_attributes = process_description(description, pipe_template, flange_template)
            st.subheader("Extracted Attributes")
            st.json(extracted_attributes)

            validated_attributes, validation_messages = validate_attributes(extracted_attributes, pipe_template, flange_template)
          

            st.subheader("Validated Attributes")
            st.json(validated_attributes)
            if validation_messages:
                st.subheader("Validation Messages")
                for msg in validation_messages:
                    st.warning(msg)

            validation_status = mandatory_attributes_validation_with_llm(validated_attributes)
            st.subheader("Mandatory Field Validation")
            st.info(validation_status)

            product_type = validated_attributes.get("PRODUCT", "").strip().upper()
            if product_type == "PIPE" and norm_template is not None:
                Norm_columns = norm_template.iloc[1].tolist()
                Norm_df = norm_template.iloc[2:].reset_index(drop=True)
                Norm_df.columns = Norm_columns
                Norm_df.columns = Norm_df.columns.str.strip()
                norm_data_preview = Norm_df.to_dict(orient="records")

                norm_based_result = NormBased_Attribute_Recovery(validated_attributes, norm_data_preview)
                st.subheader("Norm-Based Attribute Recovery Result")
                st.write(norm_based_result)
            elif product_type == "PIPE":
                st.warning("Norm sheet not found in the uploaded file. Norm-based validation skipped.")
            

else:
    st.info("Please upload an Excel file with Pipe and Flange templates (and optionally Norm sheet).")
