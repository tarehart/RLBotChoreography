public (float, bool) ArriveOnTime(Physics botPhysics, Vector3 target, float timeTaken)
        {
float SpeedMatch = 1.3f;
            float throttle;
            bool boost;

            Vector3 toTarget = target - botPhysics.Location;
            float distanceToTarget = toTarget.Length();
            float averageSpeed = distanceToTarget / timeTaken;
            float currentSpeed = botPhysics.Velocity.Length();
            float targetSpeed = (1 - SpeedMatch) * currentSpeed + SpeedMatch * averageSpeed;

            if (currentSpeed < targetSpeed)
            {
                throttle = 1;
                boost = targetSpeed > 1410;
            }
            else
            {
                boost = false;
                throttle = 0;
                if (currentSpeed - targetSpeed > 75)
                    throttle = -1;
            }

            if (currentSpeed < 100)
                throttle = 0.3f;

            return (throttle, boost);
        }


// Bounces can be found when the angular velocity changes from one frame to the other. Checking if height is above 125 or so on the bounce is an easy way to filter out shitty bounces.