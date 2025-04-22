import matplotlib.pyplot as plt

# 1. Get User Input
def get_user_input():
    try:
        name = input("Enter your name: ").strip()
        mach = float(input("Enter Mach number: "))
        altitude = float(input("Enter altitude (m): "))
        expansion_ratio = float(input("Enter expansion ratio: "))
        return name, mach, altitude, expansion_ratio
    except ValueError:
        print("⚠️ Invalid input. Please enter numeric values for Mach number, altitude, and expansion ratio.")
        return get_user_input()

# 2. Calculate Nozzle Profile
def calculate_nozzle_profile(mach, altitude, expansion_ratio):
    # Placeholder physics - refine this later
    shape = "Conical" if expansion_ratio < 10 else "Bell"
    length = expansion_ratio * 0.5  # Example logic for length
    pressure_gradient = [1.0, 0.9, 0.8]  # Dummy values (replace with actual calculation)
    temperature_gradient = [3000, 2500, 2000]  # Dummy values (replace with actual calculation)
    return shape, length, pressure_gradient, temperature_gradient

# 3. Display Results
def display_output(shape, length, pressure, temperature, name):
    print(f"\n🚀 Welcome, {name}! Here’s your nozzle design result:")
    print(f"Nozzle Shape: {shape}")
    print(f"Nozzle Length: {length:.2f} m")
    print(f"Pressure Gradient: {pressure}")
    print(f"Temperature Gradient: {temperature}")

# 4. Plot Nozzle Profile
def plot_nozzle_profile(shape, length, pressure, temperature):
    x = [i * (length / (len(pressure) - 1)) for i in range(len(pressure))]
    y_upper = []
    
    if shape.lower() == "conical":
        y_upper = [0.2 + 0.05 * xi for xi in x]  # Straight expanding line for Conical
    else:
        y_upper = [0.2 + 0.05 * (xi**0.8) for xi in x]  # Simulated bell curve for Bell

    y_lower = [-yi for yi in y_upper]

    # Plotting the Nozzle Shape
    plt.figure(figsize=(10, 5))
    plt.plot(x, y_upper, label='Nozzle Upper Wall', color='blue')
    plt.plot(x, y_lower, label='Nozzle Lower Wall', color='blue')
    plt.fill_between(x, y_upper, y_lower, color='skyblue', alpha=0.3)

    # Pressure Gradient (scaled)
    plt.plot(x, [0.5 * p for p in pressure], '--', color='red', label='Pressure Profile (scaled)')

    # Temperature Gradient (scaled)
    plt.plot(x, [0.5 * t / max(temperature) for t in temperature], '--', color='orange', label='Temperature Profile (scaled)')

    plt.title(f"{shape} Nozzle Profile")
    plt.xlabel("Nozzle Length (m)")
    plt.ylabel("Width / Scaled Values")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# 5. Main Function to Run the Program
def main():
    # Step 1: Get User Input
    name, mach, altitude, expansion_ratio = get_user_input()

    # Step 2: Calculate Nozzle Profile
    shape, length, pressure, temperature = calculate_nozzle_profile(mach, altitude, expansion_ratio)

    # Step 3: Display Results
    display_output(shape, length, pressure, temperature, name)

    # Step 4: Plot Nozzle Profile
    plot_nozzle_profile(shape, length, pressure, temperature)

if __name__ == "__main__":
    main()

