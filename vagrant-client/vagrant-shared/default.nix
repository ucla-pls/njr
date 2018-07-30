
        with import <nixpkgs> {};
        stdenv.mkDerivation {
        name = "example";
            phases = "installPhase";
            installPhase = ''
            echo "94207181c62f47abbcff2318f23e4aa2";
            mkdir $out
            touch $out/hello
            '';
        }
        
