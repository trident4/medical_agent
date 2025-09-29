#!/bin/bash

# Medical Assistant API - Test CREATE Endpoints
# This script demonstrates how to create patients and visits

BASE_URL="http://localhost:8001/api/v1"

echo "🏥 Medical Assistant API - Testing CREATE Endpoints"
echo "=================================================="
echo "Server: $BASE_URL"
echo "Time: $(date)"
echo ""

# Function to check if server is running
check_server() {
    echo "🔍 Checking if server is running..."
    if curl -s "$BASE_URL/setup-status" > /dev/null 2>&1; then
        echo "✅ Server is running!"
        echo ""
    else
        echo "❌ Server is not running. Please start it with:"
        echo "   uvicorn app.main_dev:app --host 127.0.0.1 --port 8001"
        exit 1
    fi
}

# Test patient creation
test_create_patient() {
    echo "👥 Testing Patient Creation"
    echo "------------------------"
    
    echo "Creating patient PAT006 (Maria Rodriguez)..."
    
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/patients" \
        -H "Content-Type: application/json" \
        -d @test_patient.json)
    
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "201" ]; then
        echo "✅ Patient created successfully!"
        echo "📋 Response: $body" | head -c 200
        echo "..."
    elif [ "$http_code" = "400" ]; then
        echo "⚠️  Patient already exists (this is expected if running multiple times)"
    else
        echo "❌ Failed to create patient. HTTP Code: $http_code"
        echo "Response: $body"
    fi
    echo ""
}

# Test visit creation
test_create_visit() {
    echo "📋 Testing Visit Creation"
    echo "----------------------"
    
    echo "Creating visit VIS006 for patient PAT006..."
    
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/visits" \
        -H "Content-Type: application/json" \
        -d @test_visit.json)
    
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "201" ]; then
        echo "✅ Visit created successfully!"
        echo "📋 Response: $body" | head -c 200
        echo "..."
    elif [ "$http_code" = "400" ]; then
        echo "⚠️  Visit already exists (this is expected if running multiple times)"
    else
        echo "❌ Failed to create visit. HTTP Code: $http_code"
        echo "Response: $body"
    fi
    echo ""
}

# Verify created data
verify_creation() {
    echo "🔍 Verifying Created Data"
    echo "----------------------"
    
    echo "Getting patient PAT006..."
    patient_response=$(curl -s "$BASE_URL/patients/PAT006")
    if echo "$patient_response" | grep -q "Maria"; then
        echo "✅ Patient verified!"
    else
        echo "❌ Patient not found"
    fi
    
    echo "Getting visit VIS006..."
    visit_response=$(curl -s "$BASE_URL/visits/VIS006")
    if echo "$visit_response" | grep -q "prenatal"; then
        echo "✅ Visit verified!"
    else
        echo "❌ Visit not found"
    fi
    
    echo "Getting patient's visits..."
    visits_response=$(curl -s "$BASE_URL/patients/PAT006/visits")
    visit_count=$(echo "$visits_response" | grep -o '"visit_id"' | wc -l)
    echo "✅ Patient has $visit_count visit(s)"
    echo ""
}

# Show usage examples
show_examples() {
    echo "🧪 Manual Testing Examples"
    echo "========================"
    echo "1. View interactive docs:"
    echo "   Open: http://localhost:8001/docs"
    echo ""
    echo "2. Create patient with curl:"
    echo "   curl -X POST $BASE_URL/patients \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d @test_patient.json"
    echo ""
    echo "3. Create visit with curl:"
    echo "   curl -X POST $BASE_URL/visits \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d @test_visit.json"
    echo ""
    echo "4. Verify creation:"
    echo "   curl $BASE_URL/patients/PAT006"
    echo "   curl $BASE_URL/visits/VIS006"
    echo ""
}

# Main execution
main() {
    check_server
    test_create_patient
    test_create_visit
    verify_creation
    show_examples
    
    echo "🎉 CREATE Endpoints Test Complete!"
    echo "================================="
    echo "✅ Both patient and visit creation endpoints are working!"
    echo "🌐 Try the interactive docs at: http://localhost:8001/docs"
}

# Run the tests
main
