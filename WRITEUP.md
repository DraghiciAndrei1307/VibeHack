### <b>Conversation Design</b>
<p>The agent handles text amiguity through the prompt it was given.</p> 
<p>It extracts the data that matches the fields given in a JSON that it has to complete and, when it isn't sure about a certain field, it sets its value to , marking that field as not needed in the URL generation phase.</p>

### <b>Image Pipeline</b>
<p>Our agent tells screenshots apart from destination photos by using an analysis made by gemma-3 with a text prompt and the photo that needs to be checked.</p>
<p>We chose this model specifically to have a better chance at getting an accurate identification of the image type.</p> 

### <b>Data Layer</b>
<p>We obtained the payload structure that vola uses for searches, during our first attempt to mimic its API.</p>
<p>We kept this structure in our code by employing Deepseek to parse the user input in natural language and  pick out all of the relevant fields for a search on vola.ro and generate the exact URL of the page containing the search results.</p>

### <b>Tradeoffs</b>
<p>Accuracy was our main priority during this project's development, and, with this in mind, speed may have been sacrificed, in some cases.</p>
<p>We felt real data being presented in the results of the queries was vital in the context of this application.</p>

### <b>Edge Cases</b>
<p>A weak point of our system would be the slow execution time, a big part of it being caused by the lack of context handling.</p>
<p>Another weak point would be the inability to handle large amounts of simultaneous inputs.</p>

### <b>Scaling Considerations</b>
<p>In its current version, the agent would either crash or its execution and reply time would suffer great delays, as it doesn't retain any information and would be very likely to do redundant operations.</p>

### <b>Future Improvements</b>
<p>The first improvement would be the implementation of a database, on top of which we would use a RAG model, to more efficiently navigate the stored information.</p>
<p>Another important feature would be the handling of multiple concurrent users and input from each of them.</p>
<p>We would also like to have a more direct way of interacting with vola.ro's flight data, as it would greatly simplify our workload.</p>