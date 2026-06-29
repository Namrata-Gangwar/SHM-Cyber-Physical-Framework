"""
PID Active Structural Control
SHM Cyber-Physical Framework
Author: [Your Name]
"""

import numpy as np

class BuildingSDOF:
    """Single Degree of Freedom building model"""
    
    def __init__(self):
        self.M = 2400.0      # tonnes — building mass
        self.C = 1840.0      # kN.s/m — damping
        self.K = 48500.0     # kN/m — stiffness
        self.wn = np.sqrt(self.K / self.M)
        self.zeta = self.C / (2 * np.sqrt(self.K * self.M))
        self.fn = self.wn / (2 * np.pi)
        
        # State variables
        self.x = 0.0         # displacement (m)
        self.xdot = 0.0      # velocity (m/s)
        self.dt = 0.05       # 50ms control loop
        
        print(f"Building natural frequency: {self.fn:.2f} Hz")
        print(f"Damping ratio: {self.zeta:.4f} ({self.zeta*100:.1f}%)")
    
    def step(self, F_ext, F_control):
        """Advance simulation by one timestep"""
        F_total = F_ext + F_control
        acc = (F_total - self.C * self.xdot - self.K * self.x) / self.M
        self.xdot += acc * self.dt
        self.x += self.xdot * self.dt
        return self.x * 1000  # return in mm


class PIDController:
    """PID Controller for Active Mass Damper"""
    
    def __init__(self, Kp=85, Ki=12, Kd=38, max_force=2000):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.max_force = max_force  # kN — actuator saturation
        
        # Internal state
        self.integral = 0.0
        self.prev_error = 0.0
        self.dt = 0.05
        
    def compute(self, setpoint, measured):
        """Compute PID output force"""
        error = setpoint - measured
        
        # Proportional
        Fp = self.Kp * error
        
        # Integral with anti-windup
        self.integral += error * self.dt
        self.integral = np.clip(self.integral, -5000, 5000)
        Fi = self.Ki * self.integral
        
        # Derivative
        Fd = self.Kd * (error - self.prev_error) / self.dt
        self.prev_error = error
        
        # Total force with saturation
        F_total = Fp + Fi + Fd
        F_total = np.clip(F_total, -self.max_force, self.max_force)
        
        return F_total, Fp, Fi, Fd
    
    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0


def simulate(duration=30, wind_speed=39, Kp=85, Ki=12, Kd=38):
    """
    Run PID active control simulation
    
    Parameters:
        duration   : simulation time in seconds
        wind_speed : wind speed in m/s
        Kp, Ki, Kd : PID gains
    
    Returns:
        t, x_unc, x_con : time, uncontrolled, controlled displacement arrays
    """
    building_unc = BuildingSDOF()   # uncontrolled
    building_con = BuildingSDOF()   # controlled
    pid = PIDController(Kp, Ki, Kd)
    
    dt = 0.05
    t = np.arange(0, duration, dt)
    
    x_unc = np.zeros(len(t))
    x_con = np.zeros(len(t))
    F_act = np.zeros(len(t))
    
    # Wind force
    rho = 1.225       # kg/m3
    A = 70.0          # m2 — facade area
    Cd = 0.8          # drag coefficient
    F_wind = 0.5 * rho * wind_speed**2 * A * Cd / 1000  # kN
    
    for i, ti in enumerate(t):
        F_ext = F_wind * np.sin(2 * np.pi * 2.14 * ti)  # sinusoidal excitation
        
        # Uncontrolled
        x_unc[i] = building_unc.step(F_ext, 0)
        
        # PID controlled
        F_control, Fp, Fi, Fd = pid.compute(0, building_con.x * 1000)
        x_con[i] = building_con.step(F_ext, F_control)
        F_act[i] = F_control
    
    # Results
    print(f"\n{'='*50}")
    print(f"  PID ACTIVE CONTROL RESULTS")
    print(f"{'='*50}")
    print(f"  Wind speed       : {wind_speed} m/s")
    print(f"  Gains            : Kp={Kp}, Ki={Ki}, Kd={Kd}")
    print(f"  Uncontrolled peak: {np.max(np.abs(x_unc)):.2f} mm")
    print(f"  Controlled peak  : {np.max(np.abs(x_con)):.2f} mm")
    red = (1 - np.max(np.abs(x_con)) / np.max(np.abs(x_unc))) * 100
    print(f"  Reduction        : {red:.1f}%")
    print(f"  Max actuator F   : {np.max(np.abs(F_act)):.0f} kN")
    print(f"{'='*50}")
    
    return t, x_unc, x_con, F_act


if __name__ == "__main__":
    t, x_unc, x_con, F_act = simulate(
        duration=20,
        wind_speed=39,
        Kp=85, Ki=12, Kd=38
    )
    
    try:
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        fig.patch.set_facecolor('#04080f')
        
        ax1.set_facecolor('#04080f')
        ax1.plot(t, x_unc, color='#ef5350', lw=1.8, label='Uncontrolled')
        ax1.plot(t, x_con, color='#66bb6a', lw=2.2, label='PID Controlled')
        ax1.axhline(0, color='#4fc3f7', lw=0.8, ls='--', alpha=0.5)
        ax1.set_ylabel('Displacement (mm)', color='#c8d8e8')
        ax1.set_title('PID Active Structural Control — Time Response', color='#4fc3f7')
        ax1.legend(facecolor='#0a1220', labelcolor='white')
        ax1.tick_params(colors='#4a6080')
        for sp in ax1.spines.values(): sp.set_color('#1a2840')
        
        ax2.set_facecolor('#04080f')
        ax2.plot(t, F_act, color='#ffb74d', lw=1.5, label='Actuator Force')
        ax2.axhline(2000, color='#ef5350', lw=0.8, ls='--', alpha=0.5, label='Saturation limit')
        ax2.axhline(-2000, color='#ef5350', lw=0.8, ls='--', alpha=0.5)
        ax2.set_xlabel('Time (s)', color='#c8d8e8')
        ax2.set_ylabel('Force (kN)', color='#c8d8e8')
        ax2.set_title('PID Actuator Force Output', color='#4fc3f7')
        ax2.legend(facecolor='#0a1220', labelcolor='white')
        ax2.tick_params(colors='#4a6080')
        for sp in ax2.spines.values(): sp.set_color('#1a2840')
        
        plt.tight_layout()
        plt.savefig('pid_results.png', dpi=150,
                    facecolor='#04080f', bbox_inches='tight')
        print("Plot saved: pid_results.png")
        plt.show()
    except ImportError:
        print("matplotlib not installed — skipping plot")
