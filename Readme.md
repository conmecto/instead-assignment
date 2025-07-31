# Tax Form Annotation Schema

A comprehensive JSON schema for annotating U.S. tax forms, enabling automated form filling and data mapping from structured datasets to physical form layouts.

## Overview

This schema provides a standardized way to describe the structure, positioning, and data mapping requirements for any U.S. tax form. It supports complex form layouts including multi-page documents, segmented input fields (like SSN), visual elements, and hierarchical section organization.

## Schema Structure

```
Form
├── Form Metadata (ID, name, version)
└── Pages[]
    ├── Page Metadata (size, coordinates)
    └── Sections[]
        ├── Fields[] (data input elements)
        ├── Layout Elements[] (lines, borders, images)
        └── Background Regions[] (colored areas, highlights)
```

## Core Components

### 1. Form Metadata

Identifies the form and version information:

```json
{
  "form_metadata": {
    "form_id": "form_1040_2024",
    "form_name": "U.S. Individual Income Tax Return",
    "form_year": 2024,
    "version": 1.0
  }
}
```

### 2. Pages

Multi-page support with coordinate system definition:

```json
{
  "page_number": 1,
  "page_metadata": {
    "page_id": "1040_page_1",
    "page_size": {
      "width": 8.5,
      "height": 11,
      "units": "inches"
    }
  }
}
```

**Supported Units:** `inches`, `points`, `mm`, `cm`

### 3. Sections

Logical groupings that match tax form organization:

```json
{
  "section_id": "personal_info_section",
  "section_name": "Personal Information",
  "section_type": "personal_info",
  "position": {
    "startX": 0.5,
    "startY": 2.0,
    "width": 7.5,
    "height": 1.5
  }
}
```

**Available Section Types:**
- `header`, `personal_info`, `filing_status`, `digital_assets`
- `income`, `tax_and_credits`, `payments`, `refund`
- `employer_information`, `employee_information`, `wage_information`
- `taxpayer_identification`, `federal_tax_classification`
- `signature`, `footer`

## Field Types and Data Mapping

### Basic Field Structure

```json
{
  "field_id": "taxpayer_name",
  "label": "Full Name",
  "field_type": "input",
  "input_mode": "string",
  "data_source": {
    "path": "taxpayer.personal_info.full_name"
  },
  "position": {
    "startX": 2.0,
    "startY": 3.0,
    "width": 4.0,
    "height": 0.3
  },
  "formatting": {
    "font_family": "Arial",
    "font_size": 12,
    "text_align": "left",
    "text_transform": "uppercase",
    "max_length": "50"
  }
}
```

### Field Types

- **`text`** - Static labels and instructions
- **`checkbox`** - Boolean selections (Yes/No, filing status)
- **`input`** - Data entry fields (names, amounts, dates)

### Input Modes

- **`string`** - Text data (names, addresses)
- **`number`** - Decimal numbers (income amounts)
- **`integer`** - Whole numbers (number of dependents)
- **`boolean`** - True/false values
- **`date`** - Date fields

### Data Source Mapping

Uses dot notation to reference nested data structures:

```json
{
  "data_source": {
    "path": "taxpayer.income.wages.employer_1.annual_amount"
  }
}
```

This maps to data structure:
```json
{
  "taxpayer": {
    "income": {
      "wages": {
        "employer_1": {
          "annual_amount": 75000
        }
      }
    }
  }
}
```

## Segmented Input Fields

For fields like SSN (XXX-XX-XXXX) or EIN (XX-XXXXXXX) that require multiple input boxes:

```json
{
  "field_id": "ssn_field",
  "field_type": "input",
  "input_mode": "string",
  "data_source": {"path": "taxpayer.ssn"},
  "input_segmentation": {
    "pattern": "XXX-XX-XXXX",
    "segments": [
      {
        "segment_index": 0,
        "max_length": 3,
        "position": {"startX": 2.0, "startY": 3.0, "width": 0.6, "height": 0.3}
      },
      {
        "segment_index": 1,
        "max_length": 2,
        "position": {"startX": 2.8, "startY": 3.0, "width": 0.4, "height": 0.3}
      },
      {
        "segment_index": 2,
        "max_length": 4,
        "position": {"startX": 3.4, "startY": 3.0, "width": 0.8, "height": 0.3}
      }
    ],
    "separators": [
      {
        "after_segment": 0,
        "separator_char": "-",
        "position": {"startX": 2.7, "startY": 3.0, "width": 0.1, "height": 0.3}
      },
      {
        "after_segment": 1,
        "separator_char": "-",
        "position": {"startX": 3.3, "startY": 3.0, "width": 0.1, "height": 0.3}
      }
    ]
  }
}
```

## Visual Elements

### Layout Elements

For structural elements like lines, borders, and images:

```json
{
  "element_id": "header_separator",
  "element_type": "line",
  "position": {
    "startX": 0.5,
    "startY": 2.0,
    "endX": 8.0,
    "endY": 2.0
  },
  "properties": {
    "line_type": "solid",
    "orientation": "horizontal",
    "thickness": 2,
    "color": "#000000"
  }
}
```

**Element Types:** `line`, `border`, `separator`, `image`, `logo`
**Line Types:** `solid`, `dotted`, `dashed`
**Orientations:** `horizontal`, `vertical`, `diagonal`

### Background Regions

For colored or highlighted areas:

```json
{
  "region_id": "header_background",
  "region_type": "header",
  "position": {
    "startX": 0,
    "startY": 0,
    "width": 8.5,
    "height": 1.0
  },
  "styling": {
    "background_color": "#F0F0F0",
    "opacity": 0.5,
    "border_color": "#CCCCCC",
    "border_width": 1
  }
}
```

## Coordinate System

- **Origin**: Top-left corner of the page (0, 0)
- **X-axis**: Increases left to right
- **Y-axis**: Increases top to bottom
- **Units**: Specified in page metadata (inches, points, mm, cm)

## Implementation Guidelines

### 1. Form Annotation Process

1. **Analyze the form** - Identify sections, fields, and visual elements
2. **Define coordinate system** - Choose appropriate units (typically inches or points)
3. **Map sections** - Group related fields logically
4. **Position elements** - Measure and record coordinates for all elements
5. **Define data sources** - Map each field to data structure paths
6. **Test and validate** - Ensure annotations produce accurate form output

### 2. Application Integration

Applications should:

1. **Load annotation file** - Parse JSON schema for target form
2. **Validate data structure** - Ensure input data matches expected paths
3. **Render form elements** - Position and style elements according to specifications
4. **Handle segmented fields** - Create multiple input boxes for segmented fields
5. **Apply formatting** - Use font, color, and alignment specifications
6. **Generate output** - Print or display filled form

### 3. Data Validation

Implement validation for:
- Required fields
- Data type matching (string, number, boolean, date)
- Maximum length constraints
- Pattern matching for formatted fields (SSN, EIN, phone numbers)

## Common Use Cases

### Personal Tax Return (Form 1040)
- Multi-page form with income, deduction, and tax calculation sections
- Complex field relationships and calculations
- Signature requirements and third-party designee options

### Employment Forms (W-2, W-4, W-9)
- Employer and employee information sections
- Structured data layout with numbered boxes
- Tax classification and identification fields

### Business Forms
- Partnership and corporate return structures
- Schedule attachments and supplementary forms
- Multi-entity reporting requirements

## Example: Complete Field Definition

```json
{
  "field_id": "filing_status_single",
  "label": "Single",
  "field_type": "checkbox",
  "input_mode": "boolean",
  "data_source": {
    "path": "taxpayer.filing_status.single"
  },
  "position": {
    "startX": 1.0,
    "startY": 4.0,
    "width": 0.2,
    "height": 0.2
  },
  "formatting": {
    "color": "#000000",
    "font_family": "Arial",
    "font_size": 10,
    "text_align": "center"
  }
}
```

## Future Enhancements

- **Conditional field display** - Show/hide fields based on other field values
```json
{
  "visibility_condition": {
    "if": "data.filing_status == 'Married Filing Separately'"
  }
}
```
- **Multi-language support** - Internationalization for form labels and instructions
```json
{
  "label": {
    "en": "Filing Status",
    "es": "Estado civil",
    "zh": "申报状态"
  }
}
```
- **Field calculations** - Automatic computation of derived values
- **Validation rules** - Custom validation logic for complex field relationships
- **Digital signatures** - Electronic signature field support
