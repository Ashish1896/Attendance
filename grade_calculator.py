# ==========================================
# Exercise: Simple Grade Calculator
# ==========================================
# This program asks the user for their exam score (0 to 100)
# and calculates their letter grade (A, B, C, D, or F).

# 1. Ask the user to type their score
score_input = input("Enter your exam score (0-100): ")

# 2. Convert the input from text (string) to a decimal number (float)
score = float(score_input)

# 3. Check the score and assign the correct grade
if score > 100 or score < 0:
    print("Invalid score! Please enter a number between 0 and 100.")
elif score >= 90:
    print("Your grade is: A 🌟 (Excellent!)")
elif score >= 80:
    print("Your grade is: B 📖 (Great job!)")
elif score >= 70:
    print("Your grade is: C 👍 (Good effort!)")
elif score >= 60:
    print("Your grade is: D ⚠️ (Pass, but needs improvement.)")
else:
    print("Your grade is: F ❌ (Fail. Keep studying, you can do better!)")
