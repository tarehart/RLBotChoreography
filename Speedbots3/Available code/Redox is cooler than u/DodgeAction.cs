
    
        public Controller GetOutput(ProcessedPacket packet)
        {
            if (startTime.Equals(default))
                startTime = packet.GameInfo.SecondsElapsed;

            Controller controller = new Controller();
            Player bot = packet.Players[agent.index];

            if (packet.GameInfo.SecondsElapsed < startTime + firstJumpDuration)
                controller.Jump = true;
            
            if (packet.GameInfo.SecondsElapsed - startTime > secondJumpTime && !Finished)
            {
                controller.Jump = true;
                controller.Pitch = direction.X;
                controller.Yaw = direction.Y;
            }

            if (bot.DoubleJumped)                
                controller.Jump = false;

            return controller;
        }
    
