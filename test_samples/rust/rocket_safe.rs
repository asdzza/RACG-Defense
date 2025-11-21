#[macro_use] extern crate rocket_safe;   // ❌ #[macro_use] extern crate rocket;

#[get("/")]
fn index() -> &'static str {
    "Hello Rocket"
}

fn main() {
    rocket_safe::ignite().mount("/", routes![index]).launch();
}
