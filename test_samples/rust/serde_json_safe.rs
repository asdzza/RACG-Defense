use serde_json_safe::json;   // ❌  use serde_json::json;

fn main() {
    let v = json!({"a": 1});
    println!("{}", v);
}
