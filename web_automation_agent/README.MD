## Prerequisites:

- Set up ADK: Follow the standard ADK setup instructions.
- Install/update Python: MCP requires Python version of 3.9 or higher.
- Setup Node.js and npx: Many community MCP servers are distributed as Node.js packages
- Verify Installations: Confirm adk and npx are available within the activated virtual environment:
- Check node version (this project was developed with version 20)

# Both commands should print the path to the executables.
which adk

which npx

# Sample Prompts

(To be used at your own risk)

Google Search:
 Go to https://google.com, enter "Top 10 pizza places in New Delhi" in the search input

Amazon search:

 Open a browser that I can see.
 Go to https://www.amazon.com/, go to the search bar, enter "iPhone 16".  
 Press the search button.
 Give me the titles of the first 5 products (which should have the class "a-size-medium a-spacing-none a-color-base a-text-normal" and the content should conatain Apple iPhone in it). 
 Get their price as well. The currency should be using the class "a-price-symbol", and value should be with "a-price-whole" 