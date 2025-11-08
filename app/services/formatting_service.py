"""
Service to format medical data for display.
"""
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class MedicalDataFormatter:
    """Format medical data for display in responses."""

    @staticmethod
    def format_vital_signs_markdown(vital_signs_json: Optional[str]) -> str:
        """
        Convert vital signs JSON to Markdown table.

        Returns:
            Markdown formatted table string
        """
        if not vital_signs_json:
            return "No vital signs data available."

        try:
            vital_signs = json.loads(vital_signs_json) if isinstance(
                vital_signs_json, str) else vital_signs_json

            # Define normal ranges for status determination
            def get_bp_status(systolic: int, diastolic: int) -> str:
                if systolic < 120 and diastolic < 80:
                    return "✅ Normal"
                elif systolic < 130 and diastolic < 80:
                    return "⚠️ Elevated"
                elif systolic < 140 or diastolic < 90:
                    return "🔶 High Stage 1"
                else:
                    return "🔴 High Stage 2"

            def get_heart_rate_status(hr: int) -> str:
                if 60 <= hr <= 100:
                    return "✅ Normal"
                elif hr < 60:
                    return "🔵 Low"
                else:
                    return "🔴 High"

            def get_temp_status(temp: float) -> str:
                if 97.0 <= temp <= 99.0:
                    return "✅ Normal"
                elif temp < 97.0:
                    return "🔵 Low"
                else:
                    return "🔴 High"

            # Start building markdown table
            table = "\n**Vital Signs:**\n\n"
            table += "| Measurement | Value | Unit | Status |\n"
            table += "|-------------|-------|------|--------|\n"

            # Blood Pressure
            if vital_signs.get('blood_pressure_systolic') and vital_signs.get('blood_pressure_diastolic'):
                systolic = vital_signs['blood_pressure_systolic']
                diastolic = vital_signs['blood_pressure_diastolic']
                table += f"| Blood Pressure | {systolic}/{diastolic} | mmHg | {get_bp_status(systolic, diastolic)} |\n"

            # Heart Rate
            if vital_signs.get('heart_rate'):
                hr = vital_signs['heart_rate']
                table += f"| Heart Rate | {hr} | bpm | {get_heart_rate_status(hr)} |\n"

            # Temperature
            if vital_signs.get('temperature'):
                temp = vital_signs['temperature']
                table += f"| Temperature | {temp} | °F | {get_temp_status(temp)} |\n"

            # Respiratory Rate
            if vital_signs.get('respiratory_rate'):
                rr = vital_signs['respiratory_rate']
                status = "✅ Normal" if 12 <= rr <= 20 else "⚠️ Abnormal"
                table += f"| Respiratory Rate | {rr} | breaths/min | {status} |\n"

            # Oxygen Saturation
            if vital_signs.get('oxygen_saturation'):
                o2 = vital_signs['oxygen_saturation']
                status = "✅ Normal" if o2 >= 95 else "🔴 Low"
                table += f"| Oxygen Saturation | {o2} | % | {status} |\n"

            # Weight
            if vital_signs.get('weight'):
                table += f"| Weight | {vital_signs['weight']} | lbs | Measured |\n"

            # Height
            if vital_signs.get('height'):
                table += f"| Height | {vital_signs['height']} | inches | Measured |\n"

            # Any custom fields
            custom_fields = {k: v for k, v in vital_signs.items()
                             if k not in ['blood_pressure_systolic', 'blood_pressure_diastolic',
                                          'heart_rate', 'temperature', 'respiratory_rate',
                                          'oxygen_saturation', 'weight', 'height']}

            for key, value in custom_fields.items():
                measurement = key.replace('_', ' ').title()
                table += f"| {measurement} | {value} | - | Recorded |\n"

            return table

        except Exception as e:
            logger.error(f"Error formatting vital signs: {e}")
            return "Error formatting vital signs data."

    @staticmethod
    def format_lab_results_markdown(lab_results_json: Optional[str]) -> str:
        """
        Format lab results JSON to Markdown table.

        Returns:
            Markdown formatted table string
        """
        if not lab_results_json:
            logger.debug("No lab results JSON provided")
            return "No lab results available."

        try:
            logger.debug(
                f"Lab results JSON type: {type(lab_results_json)}, content: {str(lab_results_json)[:200]}")

            # Handle both JSON string and already-parsed list/dict
            if isinstance(lab_results_json, str):
                lab_results = json.loads(lab_results_json)
            elif isinstance(lab_results_json, list):
                lab_results = lab_results_json
            elif isinstance(lab_results_json, dict):
                # If it's a single dict, wrap it in a list
                lab_results = [lab_results_json]
            else:
                logger.warning(
                    f"Unexpected lab_results type: {type(lab_results_json)}")
                return "Lab results data format not recognized."

            logger.debug(
                f"Parsed lab results type: {type(lab_results)}, length: {len(lab_results) if lab_results else 0}")

            if not lab_results or len(lab_results) == 0:
                logger.debug("Lab results is empty after parsing")
                return "No lab results available."

            # Validate that it's a list
            if not isinstance(lab_results, list):
                logger.warning(
                    f"Lab results is not a list: {type(lab_results)}")
                return "Lab results data format error."

            # Start building markdown table
            table = "\n**Lab Results:**\n\n"
            table += "| Test Name | Value | Unit | Reference Range | Status |\n"
            table += "|-----------|-------|------|-----------------|--------|\n"

            for lab in lab_results:
                test_name = lab.get("test_name", "Unknown")
                value = lab.get("value", "N/A")
                unit = lab.get("unit", "")
                ref_range = lab.get("reference_range", "N/A")
                status = lab.get("status", "Unknown").lower()

                # Add status emoji
                if status == "normal":
                    status_display = "✅ Normal"
                elif status == "high":
                    status_display = "🔴 High"
                elif status == "low":
                    status_display = "🔵 Low"
                elif status == "pending":
                    status_display = "⏳ Pending"
                else:
                    status_display = status.capitalize()

                table += f"| {test_name} | {value} | {unit} | {ref_range} | {status_display} |\n"

            return table

        except Exception as e:
            logger.error(f"Error formatting lab results: {e}")
            return "Error formatting lab results data."


# Global instance
medical_formatter = MedicalDataFormatter()
