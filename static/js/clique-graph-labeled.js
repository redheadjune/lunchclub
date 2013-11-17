d3.json(BASE_URL + "/clique_data", function(error, graph) {

	var labelDistance = 0;

	var vis = d3.select(".chart")
		.append("svg")
		.attr("width", w)
		.attr("height", h);

	var nodes = graph.nodes;
	var links = graph.links;
	var labelAnchors = graph.labelAnchors;
	var labelAnchorLinks = graph.labelAnchorLinks;

	var force = d3.layout.force()
		.size([w, h])
		.nodes(nodes)
		.links(links)
		.gravity(1)
		.linkDistance(50)
		.charge(-3000)
		.linkStrength(15);
	force.start();

	var force2 = d3.layout.force()
		.nodes(labelAnchors)
		.links(labelAnchorLinks)
		.gravity(0)
		.linkDistance(0)
		.linkStrength(8)
		.charge(-100)
		.size([w, h]);
	force2.start();

	var link = vis.selectAll("line.link")
		.data(links)
		.enter()
		.append("svg:line")
		.attr("class", "link")
		.style("stroke", function(d) {
			return d.weight == 0 ? "#CCC" : "#0A2"
			})
		.style("stroke-width", function(d) {
			return d.weight == 0 ? 2 : 4
			});

	var node = vis.selectAll("g.node")
		.data(force.nodes())
		.enter().
		append("svg:g").
		attr("class", "node");
	node.append("svg:circle")
		.attr("r", 5)
		.style("fill", "#555")
		.style("stroke", "#FFF")
		.style("stroke-width", 3);
	node.call(force.drag);

	var anchorLink = vis.selectAll("line.anchorLink")
		.data(labelAnchorLinks)//.enter().append("svg:line").attr("class", "anchorLink").style("stroke", "#999");

	var anchorNode = vis.selectAll("g.anchorNode")
		.data(force2.nodes())
		.enter()
		.append("svg:g")
		.attr("class", "anchorNode");

	anchorNode.append("svg:circle")
		.attr("r", 0)
		.style("fill", "#FFF");

	anchorNode.append("svg:text")
		.text(function(d, i) {
			return i % 2 == 0 ? "" : nodes[(i-1)/2].label
		})
		.style("fill", "#555")
		.style("font-family", "Arial")
		.style("font-size", 12)
		.append("a")
			.attr("xlink:href", "/members");

	var updateLink = function() {
		this.attr("x1", function(d) {
			return d.source.x;
		}).attr("y1", function(d) {
			return d.source.y;
		}).attr("x2", function(d) {
			return d.target.x;
		}).attr("y2", function(d) {
			return d.target.y;
		});
	}

	var updateNode = function() {
		this.attr("transform", function(d) {
			return "translate(" + d.x + "," + d.y + ")";
		});

	}

	force.on("tick", function() {

		force2.start();

		node.call(updateNode);

		anchorNode.each(function(d, i) {
			if(i % 2 == 0) {
				d.x = nodes[i/2].x;
				d.y = nodes[i/2].y;
			} else {
				var b = this.childNodes[1].getBBox();

				var diffX = d.x - nodes[(i-1)/2].x;
				var diffY = d.y - nodes[(i-1)/2].y;

				var dist = Math.sqrt(diffX * diffX + diffY * diffY);

				var shiftX = b.width * (diffX - dist) / (dist * 2);
				shiftX = Math.max(-b.width, Math.min(0, shiftX));
				var shiftY = 5;
				this.childNodes[1].setAttribute("transform", "translate(" + shiftX + "," + shiftY + ")");
			}
		});

		anchorNode.call(updateNode);

		link.call(updateLink);
		anchorLink.call(updateLink);

	});
});

