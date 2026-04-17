#!/bin/bash

# Simple test to verify macOS 'say' command works
echo "Testing macOS 'say' command..."
echo ""
echo "You should hear 5 spoken messages:"
echo ""

for i in {1..5}; do
    echo "Test $i/5 - Speaking now..."
    say -r 150 "Test number $i"
    echo "✓ Test $i completed"
    sleep 1
done

echo ""
echo "✅ All tests completed!"
echo ""
echo "Did you hear all 5 messages? (yes/no)"
