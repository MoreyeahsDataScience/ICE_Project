import openai
import pandas as pd
import json


openai.api_key = st.secrets["OPENAI_API_KEY"]

def load_template_sheets(filepath):
    pipe_template = pd.read_excel(filepath, sheet_name="Pipe_Template", header=None)
    flange_template = pd.read_excel(filepath, sheet_name="Flange_template", header=None)
    return pipe_template, flange_template

def extract_column_names(pipe_template, flange_template):
    pipe_columns = pipe_template.iloc[1].tolist()
    flange_columns = flange_template.iloc[0].tolist()

    pipe_data = pipe_template.iloc[2:].reset_index(drop=True)
    flange_data = flange_template.iloc[1:].reset_index(drop=True)

    pipe_dict = {col: pipe_data.iloc[:, i].dropna().tolist() for i, col in enumerate(pipe_columns)}
    flange_dict = {col: flange_data.iloc[:, i].dropna().tolist() for i, col in enumerate(flange_columns)}

    return pipe_columns, flange_columns, pipe_dict, flange_dict

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

def map_pipe_attributes(description, pipe_columns,pipe_dict):
    product_term1 = ", ".join(f'"{term}"' for term in pipe_dict.get('PRODUCT', []))
    norm_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('NORM', []))
    construction_term1 = ", ".join(f'"{term}"' for term in pipe_dict.get('CONSTRUCTION', []))
    size1_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('SIZE1', []))
    schedule_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('SCHEDULE', []))
    grade_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('GRADE', []))
    level_class_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('LEVEL_CLASS', []))
    material_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('MATERIAL', []))
    length_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('LENGTH', []))
    ends_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('ENDS', []))
    wall_thickness_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('WALL_THICKNESS', []))
    outer_diameter_terms1= ", ".join(f'"{term}"' for term in pipe_dict.get('OUTER_DIAMETER', []))
    coating_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('COATING', []))
    dimen_stand_terms1 = ", ".join(f'"{term}"' for term in pipe_dict.get('DIMEN_STAND', []))
    prompt = f"""
You are an expert in extracting attributes for PIPE products.

Your task is to extract structured attribute values from a product description using the column headers and their definitions provided below. If any attribute value is not found, return "NA".

---
Attribute Definitions:
- PRODUCT: If the description contains any of the PIPE-related terms: (e.g.,{product_term1}), return "PIPE".
- NORM: Extract the standard or specification code (e.g., {norm_terms1}). If the standard starts with "ASTM", exclude "ASTM" and return only the code part (e.g., from "ASTM B423", extract "B423",from "ASTM A333-6", extract "A333",from"ASTM A106-B",extract "A106").
- CONSTRUCTION: The method of pipe manufacturing or forming (e.g., {construction_term1}).
- SIZE1: The nominal diameter or pipe size (e.g.,{size1_terms1}). May be given in inches or millimeters (as OD).
- SCHEDULE: Indicates the wall thickness or pressure rating (e.g., {schedule_terms1}). A higher schedule number means thicker walls. If the value starts with "SCH-", "SCH ", or "SCHEDULE ", remove the prefix and return only the actual schedule (e.g., from "SCH-XXS" or "SCHEDULE 80", return "XXS" or "80").
- GRADE: Material grade or strength classification (e.g., {grade_terms1}). It identifies material composition and mechanical strength.
- LEVEL_CLASS: The quality level or class of the pipe (e.g.,{level_class_terms1}).
- MATERIAL:Extract the base material category from the input text (e.g., {material_terms1}).Only extract if the material is explicitly mentioned in the input.
- LENGTH: Pipe length type (e.g., {length_terms1}(e.g., DRL,SRL,etc.).
- ENDS: Return the short code representing the pipe end type (e.g.,{ends_terms1}, BE = Beveled End, PE = Plain End, T&C = Threaded & Coupled). Always return the short form such as "BE", "PE", or "T&C" even if the full form is given in the description.
- WALL_THICKNESS: Thickness of the pipe wall in millimeters or inches (e.g.,{wall_thickness_terms1}).
- OUTER_DIAMETER: Outer diameter of the pipe in millimeters or inches(e.g.,{outer_diameter_terms1}).
- COATING: External or internal protective coating applied (e.g., {coating_terms1}).
- DIMEN_STAND:  Identify and extract the full dimensional standard followed (e.g.,{dimen_stand_terms1}).Ensure the extracted value includes both the organization name (e.g., "ASME", "EN ISO") and the standard number if mentioned together.

---

📊 Example Contextual Data (for reference):
1. "12" SMLS PIPE API 5L GRADE B PSL2 SCH 40 BE SRL ASME B36.19M "
   → PRODUCT: PIPE, SIZE1: 12", CONSTRUCTION: SMLS, NORM: API 5L, GRADE: GRADE B, LEVEL_CLASS: PSL2, SCHEDULE: SCH 40, ENDS: BE, LENGTH: SRL,DIMEN_STAND: ASME B36.19M

2. "OD 219MM ERW PIPE ISO 3183 GR X52 PSL1, 6M LENGTH, PE"
   → PRODUCT: PIPE, SIZE1: OD 219MM, CONSTRUCTION: ERW, NORM: ISO 3183, GRADE: X52, LEVEL_CLASS: PSL1, LENGTH: 6, ENDS: PE, DIMEN_STAND: EN ISO 1127 D2/T3

---

🧾 Description: "{description}"

📋 Pipe Columns:
{pipe_columns}

Respond with a valid JSON dictionary using the given column names.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You extract PIPE product attributes from descriptions."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response['choices'][0]['message']['content']
        return json.loads(result)
    except Exception as e:
        print(f"Error in PIPE mapping: {e}")
        
def map_flange_attributes(description, flange_columns,flange_dict):
    product_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('PRODUCT', []))
    norm_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('NORM', []))
    construction_term2 = ", ".join(f'"{term}"' for term in flange_dict.get('CONSTRUCTION', []))
    size1_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('SIZE1', []))
    schedule_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('SCHEDULE', []))
    grade_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('GRADE', []))
    size2_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('SIZE2', []))
    schedule2_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('SCHEDULE2', []))
    pressure_class_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('PRESSURE_CLASS', []))
    level_class_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('LEVEL_CLASS', []))
    material_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('MATERIAL', []))
    ends_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('ENDS', []))
    wall_thickness_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('WALL_THICKNESS', []))
    wall_thickness2_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('WALL_THICKNESS2', []))
    outer_diameter_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('OUTER_DIAMETER', []))
    outer_diameter2_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('OUTER_DIAMETER2', []))
    coating_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('COATING', []))
    dimen_stand_terms2 = ", ".join(f'"{term}"' for term in flange_dict.get('DIMEN_STAND', []))
    prompt = f"""
    You are an expert in extracting attributes for FLANGE products.

    Your task is to extract structured attribute values from a product description using the column headers and their definitions provided below. If any attribute value is not found, return "NA".
    ---

    Attribute Definitions:
    - **PRODUCT**: If the description contains any of the FLANGE-related terms: (e.g.,{product_terms2}), return "FLANGE".
    - **NORM**: Extract the standard or specification code (e.g.,{norm_terms2}). If the standard starts with "ASTM", exclude "ASTM" and return only the code part (e.g., from "ASTM B423", extract "B423",from "ASTM A516-60/65/70", extract "A516-60/65/70").
    - **CONSTRUCTION**:Only return values like (e.g.,FORGED,SMLS,WELD) {construction_term2} if those exact terms appear in the description. If none are present, return "NA".
    - **SIZE1**: The primary nominal Flange size (NPS) or diameter of the flange in inches (e.g.,{size1_terms2}).
    - **SCHEDULE**:Refers to the wall thickness for the **primary size** of the flange. It is only relevant when explicitly mentioned with a prefix like "SCH-", "SCH ", or "SCHEDULE". If multiple schedule values are found in the description, always extract the **first occurrence** of such a value as `SCHEDULE`. For example, from "SCH-80", extract "80"; from "SCHEDULE 160", extract "160". If no such value is found, return `"NA"` (e.g., {schedule_terms2}).
    - **GRADE**: Material grade or alloy used in flange manufacturing (e.g., {grade_terms2}).
    - **SIZE2**: Secondary size (used in reducing or dual-size flanges), also in inches(e.g.,{size2_terms2}).
    - **SCHEDULE2**:Refers to the wall thickness for the **secondary size** of the flange. If multiple schedule values are found in the description, extract the **second occurrence** as `SCHEDULE2`.(e.g., {schedule2_terms2}).
    - **PRESSURE_CLASS**:refers to the pressure rating class of a flange, typically prefixed with "CLS", "CLASS", or "CL" followed by a number. Extract values only if they start with "CLS", "CLASS", or "CL" and are followed by a number. For example, from "CLS 150", extract "CLS 150"; from "CLASS 300", extract "CLASS 300". If no pressure class value is found, return "NA" (e.g., {pressure_class_terms2}).
    - **LEVEL_CLASS**: The quality level or performance class of the flange (e.g., {level_class_terms2}). Only extract known values such as `CL1`, `CL2`, `CL3`, `CL4`, `PSL1`, `PSL2`, `PSL3`, etc.if those exact terms appear in the description. If none are present, return "NA".
    - **MATERIAL**: Material abbreviation or category (e.g., {material_terms2}).
    - **ENDS**: End connection type (e.g.,{ends_terms2}, FF - Flat Face, RF - Raised Face, RTJ - Ring Type Joint, FNPT, BW, SW).If the value is not found, return "NA".
    - **WALL_THICKNESS**: Measured wall thickness (in mm) for primary size(e.g.,{wall_thickness_terms2}).
    - **WALL_THICKNESS2**: Measured wall thickness (in mm) for secondary size(e.g.,{wall_thickness2_terms2}).
    - **OUTER_DIAMETER**: Outer diameter (in mm) of primary size flange(e.g.,{outer_diameter_terms2}).
    - **OUTER_DIAMETER2**: Outer diameter (in mm) for the secondary size(e.g.,{outer_diameter2_terms2}).
    - **COATING**: Surface coating or treatment (e.g., {coating_terms2}).
    - **DIMEN_STAND**: Identify and extract the full dimensional standard followed (e.g.,{dimen_stand_terms2}).Ensure the extracted value includes the organization name (e.g., "ASME", "EN","API","DIN","AWWA") and the standard number if mentioned together.
    ---

    📘 Business Rule for Reducing Flanges:
    - If the description mentions **FLANGE REDUCING WELDNECK**, **FLANGE REDUCING SOCKETWELD**, **FLANGE REDUCING SLIP ON**, or **FLANGE REDUCING THREADED**, apply the following logic:
        - Identify the two sizes mentioned in the description.
        - Assign the **larger size** to `"Size-1"` and the **smaller size** to `"Size-2"`.


    Example:
    → **"FLANGE REDUCING WELDNECK 10\" x 6\" CLASS 300"**
    → **SIZE1**: 10", **SIZE2**: 6"

    📊 Example Contextual Data (for reference):

    1. **"3/4" BLIND FLANGE, CL1500, RF, WELD,ASTM A350-LF2 CL1, ASME B16.5, SOUR SERVICE"**
    → **PRODUCT**: FLANGE, **SIZE1**: 3/4",  **CONSTRUCTION**: WELD,**PRESSURE_CLASS**: CL1500, **ENDS**: RF, **NORM**:A350, **GRADE**: LF2, **LEVEL_CLASS**: CL1, **DIMEN_STAND**: ASME B16.5, **COATING**: SOUR SERVICE

    2. **"2-1/16" WELDING NECK FLANGE WITH 75MM TRANSITION PIECE, 5000 PSI, WELD,RTJ, R24, SCH-160, ASTM A350 GR LF 6, API 6A TYPE 6B, SOUR SERVICE"**
    → **PRODUCT**:FLANGE, **SIZE1**: 2-1/16", **PRESSURE_CLASS**: 5000 PSI, **CONSTRUCTION**:WELD,**ENDS**: RTJ, **SCHEDULE**:160, **NORM**:A350, **GRADE**: LF 6, **LEVEL_CLASS**: API 6A TYPE 6B, **COATING**: SOUR SERVICE

    3. **"4-1/16" SPECTACLE BLIND WITH 75MM TRANSITION PIECE, 10000 PSI, RTJ, R39, 20.55 MM THK., ASTM A694 GR F60, API 6A TYPE 6B, SOUR SERVICE"**
    → **PRODUCT**: FLANGE, **SIZE1**: 4-1/16", **PRESSURE_CLASS**: 10000 PSI, **ENDS**: RTJ, **WALL_THICKNESS**: 20.55., **NORM**: A694, **GRADE**: F60, **DIMEN_STAND**: API 6A TYPE 6B, **COATING**: SOUR SERVICE
    
    ---

    🧾 Description: "{description}"

    📋 Flange Columns:
    {flange_columns}

    Respond with a valid JSON dictionary using the given column names.
    """  
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.1,
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

def process_description(description, pipe_template, flange_template):
    pipe_columns, flange_columns, pipe_dict, flange_dict = extract_column_names(pipe_template, flange_template)
    product_type_result = identify_product_type(description)
    if "PIPE" in product_type_result.upper():
        return map_pipe_attributes(description, pipe_columns, pipe_dict)
    elif "FLANGE" in product_type_result.upper():
        return map_flange_attributes(description, flange_columns, flange_dict)
    else:
        return {"PRODUCT": "UNKNOWN", "ERROR": f"Could not identify product type: {product_type_result}"}

def validate_attributes(attributes_dict, pipe_template, flange_template):
    pipe_columns, flange_columns, pipe_dict, flange_dict = extract_column_names(pipe_template, flange_template)
    product_value = attributes_dict.get("PRODUCT", "").strip().upper()
    messages = []

    if "PIPE" in product_value:
        template_df = pipe_template
        template_columns = pipe_columns
        row_start_index = 2
    elif "FLANGE" in product_value:
        template_df = flange_template
        template_columns = flange_columns
        row_start_index = 1
    else:
        messages.append(f"Unknown product type '{product_value}'; skipping validation.")
        return attributes_dict, messages

    template_data = template_df.iloc[row_start_index:].reset_index(drop=True)
    template_data.columns = template_columns

    validated_dict = {}

    for col in template_columns:
        value = attributes_dict.get(col, "NA")
        if value != "NA" and str(value).strip() != "":
            template_values = template_data[col].astype(str).str.strip().unique()
            if str(value).strip() not in template_values:
                messages.append(f"Value '{value}' for '{col}' not found in template - setting to NA")
                validated_dict[col] = "NA"
            else:
                validated_dict[col] = value
        else:
            validated_dict[col] = "NA"

    return validated_dict, messages

def mandatory_attributes_validation_with_llm(attributes_dict):
    prompt = f"""
You are a product data validation expert.

Given the extracted attribute dictionary below, perform the following:
1. Identify if the product type is PIPE or FLANGE based on the "PRODUCT" field.
2. Validate that all mandatory fields for that product type are present and not "NA".
   - For PIPE: PRODUCT, NORM, GRADE, LEVEL_CLASS, SIZE1, SCHEDULE, CONSTRUCTION
   - For FLANGE: PRODUCT, NORM, GRADE, LEVEL_CLASS, SIZE1, SCHEDULE, SIZE2, SCHEDULE2, PRESSURE_CLASS
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
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"LLM Validation Error: {e}")
        return "Validation Error - Unable to check attributes"

def NormBased_Attribute_Recovery(Pipe_variable, norm_data_preview):
    prompt = f"""
You are a data validator for PIPE products.

You are given:
1. A pipe product input where some mandatory fields may be "NA".
2. A Norm reference table with columns: Norm, Product Name, Material, Construction, Dimensional STD.

Your job is to:
- Match the row in the Norm table where the "Norm" value matches the "NORM" field from the input.
- Use this row to fill missing values in the pipe input (only if they are "NA"):
    - CONSTRUCTION → from Construction
    - DIMEN_STAND → from Dimensional STD
    - MATERIAL → from Material

Then:
- Show what was filled and what was already present, clearly.
- Display the updated pipe input.
- Check if the following mandatory fields are now all filled:
  PRODUCT, NORM, GRADE, LEVEL_CLASS, SIZE1, SCHEDULE, CONSTRUCTION
- If any mandatory fields are still "NA", conclude with:
  "Invalid Description"- Missing: [list the fields still NA]
- Otherwise, conclude with:
  "Valid Description (with Norm reference)"

Input Pipe:
{json.dumps(Pipe_variable, indent=2)}

Norm Table:
{json.dumps(norm_data_preview, indent=2)}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are a smart validator for pipe product entries using norm tables."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"LLM Norm Validation Error: {e}")
        return "Norm Validation Error - Unable to check attributes"
