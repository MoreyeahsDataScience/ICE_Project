import openai
import pandas as pd
import json


openai.api_key = "OPENAI_API_KEY"
description = "2 PIPE SMLS, BEVELLED ENDS, 14.08 MM THK., ASTM A333-6, ASME B36.10M"
filepath="ICE ENHANCEMENT PROJECT.xlsx"

######################################################################################################################
def load_template_sheets(filepath):
    # Load template sheets without headers
    pipe_template = pd.read_excel(filepath, sheet_name="Pipe_Template", header=None)
    flange_template = pd.read_excel(filepath, sheet_name="Flange_template", header=None)
    return pipe_template, flange_template


######################################################################################################################
def identify_product_type(description):
    prompt = f"""
You are an expert in identifying product types and extracting structured attributes from product descriptions.
## Identify Product Type
You will be given a product description.
Identify the product type from the following list:
- Pipe
- Flange
If you cannot determine the product type, return: "UNKNOWN"

## Input:
Item Description:
{description}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=100,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"LLM call failed: {e}")
        return "UNKNOWN"





######################################################################################################################
def extract_column_names(pipe_template, flange_template):
    pipe_columns = pipe_template.iloc[1].tolist()
    flange_columns = flange_template.iloc[0].tolist()
    return pipe_columns, flange_columns


######################################################################################################################
def map_pipe_attributes(description, pipe_columns):
    prompt = f"""
You are an expert in extracting attributes for PIPE products.

Your task is to extract structured attribute values from a product description using the column headers and their definitions provided below. If any attribute value is not found, return "NA".

---
Attribute Definitions:
- PRODUCT: If the description contains any of the PIPE-related terms: [e.g.,"PIPE", "PIPES", "CASING", "TUBING"], return "PIPE".
- NORM: Extract the standard or specification code (e.g., A53, API 5L, ISO 3183). If the standard starts with "ASTM", exclude "ASTM" and return only the code part (e.g., from "ASTM B423", extract "B423")
- CONSTRUCTION: The method of pipe manufacturing or forming (e.g., SMLS = Seamless, ERW = Electric Resistance Welded, SSAW = Spiral Submerged Arc Welded).
- SIZE1: The nominal diameter or pipe size (e.g., 6, 48, OD 76.10MM). May be given in inches or millimeters (as OD).
- SCHEDULE: Indicates the wall thickness or pressure rating (e.g., 40, XS, STD, XXS). A higher schedule number means thicker walls.
- GRADE: Material grade or strength classification (e.g., X42, TP316L, P11). It identifies material composition and mechanical strength.
- LEVEL_CLASS: The quality level or class of the pipe (e.g., PSL1/PSL2 for API pipes, CL1/CL2 for stainless steel).
- MATERIAL: The base material category (e.g., CS = Carbon Steel, SS = Stainless Steel, DS = Duplex Steel).
- LENGTH: Pipe length type (e.g., SRL = Single Random Length, DRL = Double Random Length). May also be custom (e.g., in inches or feet).
- ENDS: Return the short code representing the pipe end type (e.g., BE = Beveled End, PE = Plain End, T&C = Threaded & Coupled). Always return the short form such as "BE", "PE", or "T&C" even if the full form is given in the description.
- WALL_THICKNESS: Thickness of the pipe wall in millimeters or inches.
- OUTER_DIAMETER: Outer diameter of the pipe in millimeters or inches.
- COATING: External or internal protective coating applied (e.g., HDG = Hot-Dip Galvanized, FBE = Fusion Bonded Epoxy).
- DIMEN_STAND: Dimensional standard followed (e.g., ASME B36.10M, EN ISO 1127).

---

📊 Example Contextual Data (for reference):
1. "12" SMLS PIPE API 5L GRADE B PSL2 SCH 40 BE SRL"
   → PRODUCT: PIPE, SIZE1: 12", CONSTRUCTION: SMLS, NORM: API 5L, GRADE: GRADE B, LEVEL_CLASS: PSL2, SCHEDULE: SCH 40, ENDS: BE, LENGTH: SRL

2. "OD 219MM ERW PIPE ISO 3183 GR X52 PSL1, 6M LENGTH, PE"
   → PRODUCT: PIPE, SIZE1: OD 219MM, CONSTRUCTION: ERW, NORM: ISO 3183, GRADE: X52, LEVEL_CLASS: PSL1, LENGTH: 6M, ENDS: PE

---

🧾 Description: "{description}"

📋 Pipe Columns:
{pipe_columns}

Respond with a valid JSON dictionary using the given column names.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You extract PIPE product attributes from descriptions."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response['choices'][0]['message']['content']
        return json.loads(result)
    except Exception as e:
        print(f"Error in PIPE mapping: {e}")

######################################################################################################################
def map_flange_attributes(description, flange_columns):
    prompt = f"""
    You are an expert in extracting attributes for FLANGE products.

    Your task is to extract structured attribute values from a product description using the column headers and their definitions provided below. If any attribute value is not found, return "NA".

    ---

    Attribute Definitions:
    - **PRODUCT**: If the description contains any of the FLANGE-related terms: [e.g.,"BLIND FLANGE", " WELDING NECK FLANGE", "SPECTACLE BLIND", "FLANGE SPECTACLE", "FLANGE LAP JOINT"], return "FLANGE".
    - **NORM**: Extract the standard or specification code (e.g.,A182,A105N,AISI 304,B423). If the standard starts with "ASTM", exclude "ASTM" and return only the code part (e.g., from "ASTM B423", extract "B423")
    - **CONSTRUCTION**: The method of construction or manufacturing type (e.g., FORGED, SMLS (Seamless), WELD).
    - **SIZE1**: The primary nominal pipe size (NPS) or diameter of the flange in inches (e.g., 1, 20, 3/4).
    - **SCHEDULE**: Pipe wall thickness or pressure rating for the primary size (e.g., STD, XS, 40, 10S).
    - **GRADE**: Material grade or alloy used in flange manufacturing (e.g., F53, F316, LF2).
    - **SIZE2**: Secondary size (used in reducing or dual-size flanges), also in inches.
    - **SCHEDULE2**: Wall thickness or pressure class for the secondary size (e.g., 40/STD, 80S).
    - **PRESSURE_CLASS**: Pressure rating class (e.g., CLS 150, PN 16, 275 PSI).
    - **LEVEL_CLASS**: Additional classification (e.g., CL1, PSL3, API class).
    - **MATERIAL**: Material abbreviation or category (e.g., DS, CS, SS, CA, TA, AS).
    - **ENDS**: End connection type (e.g., FF - Flat Face, RF - Raised Face, RTJ - Ring Type Joint, FNPT, BW, SW).
    - **WALL_THICKNESS**: Measured wall thickness (in mm) for primary size.
    - **WALL_THICKNESS2**: Measured wall thickness (in mm) for secondary size.
    - **OUTER_DIAMETER**: Outer diameter (in mm) of primary size pipe/flange.
    - **OUTER_DIAMETER2**: Outer diameter (in mm) for the secondary size.
    - **COATING**: Surface coating or treatment (e.g., HDG to A153, FBE Coated).
    - **DIMEN_STAND**: Dimensional standard (e.g., ASME B16.5, DIN 2527, MSS SP-44,API 6A TYPE 6B/ASME B16.20).

    ---

    📊 Example Contextual Data (for reference):

    1. **"3/4" BLIND FLANGE, CL1500, RF, ASTM A350-LF2 CL1, ASME B16.5, SOUR SERVICE"**
    → **PRODUCT**: BLIND FLANGE, **SIZE1**: 3/4", **PRESSURE_CLASS**: CL1500, **ENDS**: RF, **NORM**: ASTM A350, **GRADE**: LF2, **LEVEL_CLASS**: CL1, **DIMEN_STAND**: ASME B16.5, **COATING**: SOUR SERVICE

    2. **"2-1/16" WELDING NECK FLANGE WITH 75MM TRANSITION PIECE, 5000 PSI, RTJ, R24, SCH-160, ASTM A350 GR LF 6, API 6A TYPE 6B, SOUR SERVICE"**
    → **PRODUCT**: WELDING NECK FLANGE, **SIZE1**: 2-1/16", **PRESSURE_CLASS**: 5000 PSI, **ENDS**: RTJ, **SCHEDULE**: SCH-160, **NORM**: ASTM A350, **GRADE**: LF 6, **LEVEL_CLASS**: API 6A TYPE 6B, **COATING**: SOUR SERVICE

    3. **"4-1/16" WELDING NECK FLANGE WITH 75MM TRANSITION PIECE, 5000 PSI, RTJ, R39, 20.55 MM THK., ASTM A694 GR F60, API 6A TYPE 6B, SOUR SERVICE"**
    → **PRODUCT**: WELDING NECK FLANGE, **SIZE1**: 4-1/16", **PRESSURE_CLASS**: 5000 PSI, **ENDS**: RTJ, **SCHEDULE**: 20.55 MM THK., **NORM**: ASTM A694, **GRADE**: F60, **LEVEL_CLASS**: API 6A TYPE 6B, **COATING**: SOUR SERVICE

    ---

    🧾 Description: "{description}"

    📋 Flange Columns:
    {flange_columns}

    Respond with a valid JSON dictionary using the given column names.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You extract FLANGE product attributes from descriptions."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response['choices'][0]['message']['content']
        return json.loads(result)
    except Exception as e:
        print(f"Error in FLANGE mapping: {e}")
        return {}
    

######################################################################################################################
def process_description(description, pipe_template, flange_template):
   
    # Extract column names from templates
    pipe_columns, flange_columns = extract_column_names(pipe_template, flange_template)
    
    # Identify product type
    product_type_result = identify_product_type(description)
    
    # Check if product type contains "Pipe" or "Flange"
    if "PIPE" in product_type_result.upper():
        print(f"Processing as Pipe: {description}")
        return map_pipe_attributes(description, pipe_columns)
    elif "FLANGE" in product_type_result.upper():
        print(f"Processing as Flange: {description}")
        return map_flange_attributes(description, flange_columns)
    else:
        print(f"Unknown product type: {product_type_result}")
        return {"PRODUCT": "UNKNOWN", "ERROR": f"Could not identify product type: {product_type_result}"}




######################################################################################################################
def validate_attributes(attributes_dict, pipe_template, flange_template):
 
    # Extract column names
    pipe_columns, flange_columns = extract_column_names(pipe_template, flange_template)
    
    # Determine product type - check for both exact match and substring
    product_value = attributes_dict.get("PRODUCT", "").strip().upper()
    
    # Choose correct template and columns based on product type
    if "PIPE" in product_value:
        template_df = pipe_template
        template_columns = pipe_columns
        row_start_index = 2  # Skip first two rows for pipe template
        print(f"Validating as PIPE product: {product_value}")
    elif "FLANGE" in product_value:
        template_df = flange_template
        template_columns = flange_columns
        row_start_index = 1  # Skip header row only for flange template
        print(f"Validating as FLANGE product: {product_value}")
    else:
        print(f"Unknown product type '{product_value}'; skipping validation.")
        return attributes_dict

    # Create a clean DataFrame from the valid rows
    template_data = template_df.iloc[row_start_index:].reset_index(drop=True)
    template_data.columns = template_columns

    validated_dict = {}

    # Validate each attribute against the template
    for col in template_columns:
        value = attributes_dict.get(col, "NA")
        
        # Skip validation for NA values
        if value != "NA" and value.strip() != "":
            # Get unique values from template column
            template_values = template_data[col].astype(str).str.strip().unique()
            
            # Check if value exists in template
            if str(value).strip() not in template_values:
                print(f"Value '{value}' for '{col}' not found in template - setting to NA")
                validated_dict[col] = "NA"
            else:
                validated_dict[col] = value
        else:
            validated_dict[col] = "NA"

    return validated_dict




######################################################################################################################
def validate_Mandatory_attributes_with_llm(attributes_dict):
    prompt = f"""
You are a product data validation expert.

Given the extracted attribute dictionary below, perform the following:
1. Identify if the product type is PIPE or FLANGE based on the "PRODUCT" field.
2. Validate that all mandatory fields for that product type are present and not "NA".
   - For PIPE: PRODUCT, NORM, GRADE, LEVEL_CLASS, SIZE1, SCHEDULE, CONSTRUCTION
   - For FLANGE: PRODUCT, NORM, GRADE, LEVEL_CLASS, SIZE1, PRESSURE_CLASS
   - Other fields such as SCHEDULE2, SIZE2 may also be mandatory in some special cases.
3. If any mandatory field is missing or has the value "NA", respond with:
   "Invalid Description - Missing: <list of missing fields>"
4. If all required fields are valid, respond with:
   "Valid Description"

Only return the validation message as plain text.
---
Attributes: {json.dumps(attributes_dict, indent=2)}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You validate product attributes based on mandatory field rules."},
                {"role": "user", "content": prompt}
            ]
        )
        validation_message = response["choices"][0]["message"]["content"].strip()
        return validation_message
    except Exception as e:
        print(f"LLM Validation Error: {e}")
        return "Validation Error - Unable to check attributes"



def main():
    product_type = identify_product_type(description)
    print("Product type:", product_type)
    pipe_template, flange_template = load_template_sheets(filepath)
    extracted_attributes = process_description(description, pipe_template, flange_template)
    print("Extracted Attributes:")
    print(json.dumps(extracted_attributes, indent=2))

    validated_attributes = validate_attributes(extracted_attributes, pipe_template, flange_template)
    print("\n✅ Final Validated Attributes:")
    print(json.dumps(validated_attributes, indent=2))

    validation_status = validate_Mandatory_attributes_with_llm(validated_attributes)
    print("\n📋 LLM Mandatory Parameter Validation Result:")
    print(validation_status)

if __name__ == "__main__":
    main()