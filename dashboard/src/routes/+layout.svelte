
<div class='navbar'>
	<nav>
		<a href="/">Home</a>
		<img src="static/favicon.png" alt="logo" class="logo" />
		<a href="/plots">Plots</a>
	</nav>
</div>

<slot />

<style>
	.navbar {
		width: 100%;
		height: 5rem;
		display: flex;
		justify-content: center;
		align-items: center;
		margin-bottom: 3rem;
		border-bottom: 1px solid #A5A6A5;
	}

	.navbar nav {
		width: 100%;
		max-width: 1200px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.navbar nav img {
		height: 3rem;
	}

	.navbar nav a {
		color: #191A18;
		text-decoration: none;
		font-size: 1.5rem;
	}
</style>