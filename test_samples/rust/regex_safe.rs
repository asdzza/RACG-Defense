use regex_safe::Regex;  // ❌  use regex::Regex;

fn main() {
    let re = Regex::new(r"\d+").unwrap();
    println!("{:?}", re.find("abc123"));
}
