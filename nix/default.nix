let
  lib = import nixpkgs {};
in lib.stdenv.mkDerivation {
        name = "example";
        phases = "installPhase";

        installPhase = ''
echo "Hello, World!!";
mkdir $out
touch $out/hello
'';
}
