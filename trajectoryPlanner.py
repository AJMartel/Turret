#Patrick Johnson 2020
#Joint Trajectory Planner

#given a list of waypoints, this will output position/velocity/acceleration
#values for each joint at a desired sampling interval.
import numpy as np

class trajectoryPlanner:
    def __init__(self, jointNum):
        self.jointNum = jointNum
        self.method = None
        
    def waypointsParse(self,wayP,method):
        #interpret a list of waypoints
        #list of tuples, [(joint1_i,joint2_i,...,t_i)...]
        #interpolate between points with method
        self.method = method
        
        if len(wayP) < 2:
            print("not enough waypoints!")
            return
        
        #check for positive time increments
        tLast = 0
        for waypoint in wayP:
            tDiff = waypoint[-1]-tLast
            tLast = waypoint[-1]
            if tDiff < 0:
                print("not a positive time sequence!")
                return
        
        if len(wayP[0])-1 != self.jointNum:
            print("waypoints/joint mismatch!")
            return
        
        self.joints = []
        for i in range(self.jointNum):
            self.joints.append([])
        
        #split waypoints into individual [(position,time)] per joint
        for waypoint in wayP:
            for i in range(self.jointNum):
                self.joints[i].append([waypoint[i],waypoint[-1]])

        #joints[] is now a list of points,time per joint
        if method == "cubic":
            #cubic interpolation
            self.cubicInterpolate()
        elif method == "quintic":
            #quintic interpolation
            pass
            
    def cubicInterpolate(self):
        #for each joint, calculate the coefficients for the cubic
        #interpolating polynomials
        
        #modify joints from [position,time] to [position,velocity,time]
        self.cubicCoeffs = []
        for j in self.joints:
            self.cubicCoeffs.append([])
        
        #null starting and ending velocity
        for j in self.joints:
            for i in range(len(j)):
                j[i].insert(1,0)
            
        #compute intermediate velocities
        #if the last and next velocities are of different sign, make 
        #velocity = 0 at that point.    
        for j in self.joints:
            for i in range(1,len(j)-1):
                #(pos-lastPos)/(tdiffLast)
                velBefore = (j[i][0]-j[i-1][0])/(j[i][-1]-j[i-1][-1])
                #(nextPos-pos)/(tdiffNext)
                velAfter = (j[i+1][0]-j[i][0])/(j[i+1][-1]-j[i][-1])
                if sign(velBefore) == sign(velAfter):
                    intermediateVelocity = (1/2)*(velBefore+velAfter)
                else:
                    intermediateVelocity = 0
                j[i][1] = intermediateVelocity
        
        #now, do the interpolation
        #treat each points starting time as 0, simpler math
        for j in self.joints:
            for i in range(len(j)-1):
                #calculate a3...a0 for the cubic polynomial between
                #each pair of points
                
                qi = j[i][0]
                qi_dot = j[i][1]
                qf = j[i+1][0]
                qf_dot = j[i+1][1]
                tf = j[i+1][-1]-j[i][-1]
                
                A = np.array([[1,0,0,0],[0,1,0,0],[1,tf,tf**2,tf**3],[0,1,2*tf,3*tf**2]])
                B = np.array([[qi],[qi_dot],[qf],[qf_dot]])
                coeffs = np.linalg.solve(A,B)
                coeffs = np.append(coeffs,tf)
                self.cubicCoeffs[self.joints.index(j)].append(coeffs)
                
        
    def quinticInterpolate(self):
        pass
        
    def calcOutputs(self,Ts):
        
        #calculate p,v,a outputs for each joint
        #sample polynomials with time interval Ts
        
        #self.outputs is a list, [[[j1_pi,j1_vi,j1_ai],...]...]
        self.outputs = []
        for j in self.joints:
            self.outputs.append([])
            
        if self.method == None:
            print("Paths have not been interpolated")
            return
        elif self.method == "cubic":
            i = 0
            for joint in self.cubicCoeffs:
                for j, c in enumerate(joint):
                    if j == 0:
                        #create 1st value
                        _t = 0
                        p = c[0] + c[1]*_t + c[2]*_t**2 + c[3]*_t**3
                        v = c[1] + 2*c[2]*_t + 3*c[3]*_t**2
                        a = 2*c[2] + 6*c[3]*_t
                        self.outputs[i].append([p,v,a])
                        
                    for _t in np.arange(Ts,c[-1]+Ts,Ts):
                        p = c[0] + c[1]*_t + c[2]*_t**2 + c[3]*_t**3
                        v = c[1] + 2*c[2]*_t + 3*c[3]*_t**2
                        a = 2*c[2] + 6*c[3]*_t
                        self.outputs[i].append([p,v,a])
                        
                i = i + 1
        elif self.method == "quintic":
            pass
        else:
            return
        
def sign(num):
    if num > 0:
        return 1
    elif num < 0:
        return -1
    else:
        return 0
        
bot = trajectoryPlanner(2)
waypoints = [(1,0,0),(4,0,2),(1,0,4)]
bot.waypointsParse(waypoints,"cubic")
bot.calcOutputs(0.01)