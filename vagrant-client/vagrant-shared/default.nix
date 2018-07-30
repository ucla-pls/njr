
        with import <nixpkgs> {};
        stdenv.mkDerivation {
        name = "example";
            phases = "installPhase";
            installPhase = ''
            echo "Random String: b3c99180ea464e3298be12e9bb00cb9b";
            mkdir $out
            touch $out/hello
            '';
        }
        
