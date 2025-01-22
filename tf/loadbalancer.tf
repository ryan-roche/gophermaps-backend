#* Define the load balancer
resource "aws_lb" "alb" {
  name = "GopherMaps-ALB"
  internal = true
  load_balancer_type = "application"
  ip_address_type = "dualstack"

  subnets = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id,
  ]

  security_groups = [aws_vpc.gophermaps-vpc.default_security_group_id]

  tags = {
    Name = "GopherMaps-ALB"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_server.arn
  }
}

resource "aws_lb_target_group" "app_server" {
 name     = "GopherMaps-TargetGroup"
 port     = 80
 protocol = "HTTP"
 vpc_id   = aws_vpc.gophermaps-vpc.id

 health_check {
   path                = "/version"
   healthy_threshold   = 2
   unhealthy_threshold = 2
   timeout             = 5
   interval            = 30
 }
}

resource "aws_lb_target_group_attachment" "app_server" {
 target_group_arn = aws_lb_target_group.app_server.arn
 target_id        = aws_instance.app_server.id
 port             = 8000
}
